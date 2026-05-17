from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Iterator, List
from uuid import uuid4

from pydantic import ValidationError

from app.core.config import get_settings
from app.repositories.topic_idea_repository import TopicIdeaRepository, topic_idea_repository
from app.schemas.common import Platform, TopicIdea, TopicIdeaGenerateRequest
from app.services.ai_provider_service import ai_provider_service
from app.services.topic_evidence_service import TopicEvidenceService, topic_evidence_service


PROMPT_VERSION = "v0.2"


class TopicIdeaGenerationService:
    def __init__(self, topic_repository: TopicIdeaRepository, evidence_service: TopicEvidenceService) -> None:
        self.topic_repository = topic_repository
        self.evidence_service = evidence_service

    def stream_topic_idea_events(self, request: TopicIdeaGenerateRequest) -> Iterator[str]:
        # 生成 generation id
        generation_id = f"gen_{uuid4().hex[:10]}"
        settings = get_settings()
        # 获得大模型的 适配器名称
        provider_name = settings.llm_provider
        # 获取大模型名称
        model_name = settings.deepseek_model if provider_name == "deepseek" else None
        generation_started = False
        try:
            # 把 request 这个 Pydantic 模型对象，转成一个适合 JSON 返回/存储的 dict
            accepted_payload = request.model_dump(by_alias=True, mode="json")
            accepted_payload["providerDiagnostics"] = self._provider_diagnostics()
            # 组装审计记录
            '''
            record = {
                "id": generation_id,
                "workspaceId": workspace_id,
                "workflow": "topic-ideas",
                "provider": provider,
                "model": model,
                "promptVersion": prompt_version,
                "inputPayload": input_payload,
                "evidenceIds": [],
                "outputPayload": None,
                "error": None,
                "status": "running",
            }
            字段含义大概是：
            id：本次生成 ID，比如 gen_xxx。
            workspaceId：哪个工作区发起的。
            workflow：固定是 topic-ideas，表示这是选题生成流程。
            provider：当前配置的 LLM provider，比如 mock 或 deepseek。
            model：如果是 DeepSeek，会记录模型名；mock 时通常是 None。
            promptVersion：当前提示词/生成逻辑版本，例如 v0.2。
            inputPayload：用户请求体，包含 direction、platforms、goal、count、audience 等。
            evidenceIds：一开始为空，因为还没召回证据。
            outputPayload：一开始为空，因为还没生成结果。
            error：一开始为空。
            status：一开始是 running。
            '''
            # 在 ai_generations 里面生成记录
            self.topic_repository.record_generation_started(
                generation_id=generation_id,
                workspace_id=request.workspace_id,
                provider=provider_name,
                model=model_name,
                prompt_version=PROMPT_VERSION,
                input_payload=accepted_payload,
                strict=True,
            )
            generation_started = True

            yield self._sse_event(
                "start",
                {
                    "workflow": "topic-ideas",
                    "generationId": generation_id,
                    "promptVersion": PROMPT_VERSION,
                    "providerDiagnostics": accepted_payload["providerDiagnostics"],
                    "acceptedPayload": accepted_payload,
                },
            )
            yield self._progress("parse_request", "已解析选题方向、平台和目标。")

            '''
                {
                    'workspaceId': 'ws_northstar', 
                    'workspaceName': '北极星内容组', 
                    'accountName': '抖音 · 程序员老陈', 
                    'platformScope': ['douyin'], 
                    'workspaceContextSource': 'postgres'
                }
            '''
            # 加载账号 和 工作区的内容
            workspace_context = self.evidence_service.load_workspace_context(request)
            accepted_payload["workspaceContextSource"] = workspace_context.get("workspaceContextSource")
            yield self._progress("load_workspace_context", "已加载工作区和账号上下文。")

            # 读取当前方向相关内容、账号高表现参考和避坑反例。
            # 下面是把前面筛出来的候选内容，整理成最终返回给选题生成模型的“三层证据包”。
            '''
                {
                    "relatedContents": related_contents, # 当前方向相关的正向参考
                    "topPerformers": top_performers,   # 账号历史高表现风格参考
                    "contrastContents": contrast_contents, # 当前方向相关但表现较弱的避坑反例
                    "retrievalDiagnostics": diagnostics,  # 本次召回和过滤过程的调试信息
                }
            '''
            content_evidence = self.evidence_service.load_topic_content_evidence(request)
            yield self._progress("load_topic_content_evidence", "已读取分层历史内容证据。")
            # 取长期记忆证据
            evidence = self.evidence_service.retrieve_topic_memories(request)
            accepted_payload["dataSourceMode"] = self.evidence_service.data_source_mode
            accepted_payload["contentRetrievalDiagnostics"] = content_evidence.get("retrievalDiagnostics", {})
            self.topic_repository.update_generation_input(generation_id, accepted_payload, strict=True)
            if request.include_evidence:
                yield self._sse_event("evidence", {"items": evidence})
            yield self._progress("retrieve_topic_memories", "已召回相似历史内容和长期记忆。")

            pattern_summary = self._analyze_patterns(content_evidence, evidence)
            yield self._progress("analyze_patterns", "已分析高低表现模式和搜索承接机会。")

            # 调用大模型 生成话题
            ideas = self.generate_topic_ideas(
                request=request,
                generation_id=generation_id,
                workspace_context=workspace_context,
                content_evidence=content_evidence,
                evidence=evidence,
                pattern_summary=pattern_summary,
            )
            yield self._progress("generate_candidates", f"已生成 {len(ideas)} 个候选选题。")

            ranked_ideas = sorted(ideas, key=lambda idea: idea.predicted_score, reverse=True)
            yield self._progress("score_candidates", "已完成选题评分和优先级排序。")

            self.topic_repository.save_generated_ideas(ranked_ideas, source_payload=accepted_payload, strict=True)
            yield self._progress("persist_topic_ideas", "已写入 PostgreSQL 选题池和审计边界。")

            for idea in ranked_ideas:
                yield self._sse_event("topic_idea", idea.model_dump(by_alias=True, mode="json"))

            output_payload = {
                "generationId": generation_id,
                "count": len(ranked_ideas),
                "topicIdeas": [idea.model_dump(by_alias=True, mode="json") for idea in ranked_ideas],
            }
            self.topic_repository.record_generation_succeeded(
                generation_id=generation_id,
                evidence_ids=self._evidence_ids(evidence),
                output_payload=output_payload,
                strict=True,
            )
            yield self._sse_event(
                "done",
                output_payload,
            )
        except Exception as exc:
            if generation_started:
                try:
                    self.topic_repository.record_generation_failed(generation_id, str(exc), strict=True)
                except Exception:
                    pass
            yield self._sse_event(
                "error",
                {
                    "generationId": generation_id,
                    "code": exc.__class__.__name__,
                    "message": str(exc),
                },
            )

    def generate_topic_ideas(
        self,
        request: TopicIdeaGenerateRequest,
        generation_id: str | None = None,
        workspace_context: Dict[str, Any] | None = None,
        content_evidence: Dict[str, Any] | None = None,
        evidence: List[Dict[str, Any]] | None = None,
        pattern_summary: Dict[str, Any] | None = None,
    ) -> List[TopicIdea]:
        generation_id = generation_id or f"gen_{uuid4().hex[:10]}"
        workspace_context = workspace_context or self.evidence_service.load_workspace_context(request)
        content_evidence = content_evidence or self.evidence_service.load_topic_content_evidence(request)
        evidence = evidence or self.evidence_service.retrieve_topic_memories(request)
        pattern_summary = pattern_summary or self._analyze_patterns(content_evidence, evidence)

        provider = ai_provider_service.get_required_chat_provider()
        provider_output = provider.generate_json(
            task="topic_ideas",
            system_prompt=self._system_prompt(),
            user_input=request.direction,
            context={
                "direction": request.direction,
                "workspace": workspace_context,
                "accountIds": request.account_ids,
                "platforms": [platform.value for platform in request.platforms],
                "goal": request.goal,
                "count": request.count,
                "audience": request.audience,
                "constraints": request.constraints,
                "contentEvidence": content_evidence,
                "evidence": evidence,
                "patternSummary": pattern_summary,
                "dataSourceMode": self.evidence_service.data_source_mode,
                "styleRules": self._style_rules(request),
            },
            schema=self._candidate_schema(),
        )
        candidates = provider_output.get("candidates", [])
        if not isinstance(candidates, list) or not candidates:
            raise RuntimeError("DeepSeek returned no topic idea candidates")
        return self._coerce_candidates(request, generation_id, candidates, evidence, content_evidence)

    def _coerce_candidates(
        self,
        request: TopicIdeaGenerateRequest,
        generation_id: str,
        candidates: List[Dict[str, Any]],
        evidence: List[Dict[str, Any]],
        content_evidence: Dict[str, Any],
    ) -> List[TopicIdea]:
        ideas: List[TopicIdea] = []
        source_candidates = candidates[: request.count]

        for index, candidate in enumerate(source_candidates):
            candidate_id = self._candidate_id(request.direction, index)
            visible_evidence = evidence[:3] if request.include_evidence else []
            data = {
                "id": candidate.get("id") or candidate_id,
                "title": candidate.get("title") or f"{request.direction}的第 {index + 1} 个选题",
                "topic": candidate.get("topic") or request.direction,
                "angle": candidate.get("angle") or "从历史内容表现和受众问题中提炼可拍角度。",
                "category": candidate.get("category") or "topic_radar",
                "targetAudience": candidate.get("targetAudience") or request.audience or "目标受众",
                "targetPlatforms": candidate.get("targetPlatforms") or [platform.value for platform in request.platforms],
                "predictedScore": self._score(candidate.get("predictedScore"), 82, index),
                "seoScore": self._score(candidate.get("seoScore"), 80, index),
                "audienceScore": self._score(candidate.get("audienceScore"), 78, index),
                "difficultyScore": self._score(candidate.get("difficultyScore"), 42, index, descending=False),
                "risk": candidate.get("risk") or "如果没有真实经历或评论问题支撑，容易变成泛泛建议。",
                "recommendReason": candidate.get("recommendReason")
                or self._default_recommend_reason(content_evidence, evidence),
                "evidenceCount": len(evidence),
                "evidence": visible_evidence,
                "suggestedTitles": candidate.get("suggestedTitles") or [candidate.get("title") or request.direction],
                "suggestedHooks": candidate.get("suggestedHooks") or [f"今天不讲概念，只拆一个和{request.direction}有关的真实选择。"],
                "suggestedTags": candidate.get("suggestedTags") or self._default_tags(request),
                "nextActions": candidate.get("nextActions") or ["generate_titles", "generate_script", "save_to_topic_pool"],
                "generationId": generation_id,
            }
            try:
                ideas.append(TopicIdea(**data))
            except ValidationError:
                data["targetPlatforms"] = [platform.value for platform in request.platforms] or [Platform.douyin.value]
                ideas.append(TopicIdea(**data))

        return ideas

    def _fallback_candidates(
        self,
        request: TopicIdeaGenerateRequest,
        evidence: List[Dict[str, Any]],
        content_evidence: Dict[str, Any] | None = None,
    ) -> List[Dict[str, Any]]:
        content_evidence = content_evidence or {}
        related_contents = content_evidence.get("relatedContents", [])
        top_performers = content_evidence.get("topPerformers", [])
        contrast_contents = content_evidence.get("contrastContents", [])
        platforms = [platform.value for platform in request.platforms]
        playbooks = [
            ("真实复盘", "拿一个具体经历或历史作品做拆解，不做泛泛路线图。"),
            ("评论问题", "从观众最可能追问的一句话切入，给出判断标准。"),
            ("搜索承接", "围绕一个明确搜索词回答“什么时候该做/不该做”。"),
            ("避坑反例", "对照低表现或高风险表达，讲清楚不要怎么拍。"),
            ("成本账", "把时间、钱、技能门槛拆开，给出可执行取舍。"),
            ("第一步", "只讲可验证的第一步，让用户当天能试一次。"),
            ("对比选择", "把两个常见路径放在同一场景里比较。"),
            ("素材清单", "给出拍摄所需案例、截图、评论和数据素材。"),
            ("脚本实验", "设计一个低成本 A/B 选题实验。"),
            ("复拍优化", "从历史高表现内容里抽一处结构复用到新方向。"),
        ]
        return [
            {
                "title": self._fallback_title(request.direction, playbook, index, related_contents, top_performers),
                "topic": request.direction,
                "angle": self._fallback_angle(playbook, related_contents, top_performers, contrast_contents, index),
                "category": "fallback_topic",
                "targetAudience": request.audience or "普通创作者的核心受众",
                "targetPlatforms": platforms,
                "predictedScore": max(70, 86 - index * 2 + min(len(related_contents), 4)),
                "seoScore": max(68, 82 - index + min(len(related_contents), 3)),
                "audienceScore": max(68, 83 - index + min(len(evidence), 3)),
                "difficultyScore": 35 + index * 2,
                "risk": "素材不够具体时不要硬上结论，先补一个真实案例或评论截图。",
                "recommendReason": self._default_recommend_reason(content_evidence, evidence),
                "suggestedTitles": [self._fallback_title(request.direction, playbook, index, related_contents, top_performers)],
                "suggestedHooks": [self._fallback_hook(request.direction, playbook, related_contents, index)],
                "suggestedTags": self._default_tags(request),
                "nextActions": ["generate_titles", "generate_script", "save_to_topic_pool"],
            }
            for index in range(request.count)
            for playbook in [playbooks[index % len(playbooks)]]
        ]

    def _analyze_patterns(self, content_evidence: Dict[str, Any], evidence: List[Dict[str, Any]]) -> Dict[str, Any]:
        related_contents = content_evidence.get("relatedContents", [])
        top_performers = content_evidence.get("topPerformers", [])
        contrast_contents = content_evidence.get("contrastContents", [])
        diagnostics = content_evidence.get("retrievalDiagnostics", {})
        top_content = top_performers[0] if top_performers else {}
        related_content = related_contents[0] if related_contents else {}
        return {
            "topContentTitle": top_content.get("title"),
            "topContentScore": top_content.get("score"),
            "topContentViews": top_content.get("views"),
            "topContentCompletionRate": top_content.get("completionRate"),
            "topRelatedContentTitle": related_content.get("title"),
            "topRelatedMatchedTerms": related_content.get("matchedTerms", []),
            "relatedContentCount": len(related_contents),
            "contrastContentCount": len(contrast_contents),
            "evidenceCount": len(evidence),
            "contentRetrievalStrategy": diagnostics.get("strategy"),
            "relatedTitles": [item.get("title") for item in related_contents[:5] if item.get("title")],
            "topPerformerTitles": [item.get("title") for item in top_performers[:5] if item.get("title")],
            "avoidTitles": [item.get("title") for item in contrast_contents[:3] if item.get("title")],
            "recommendation": "优先选择能承接搜索词、评论问题和账号人设的选题。",
        }

    def _default_recommend_reason(self, content_evidence: Dict[str, Any], evidence: List[Dict[str, Any]]) -> str:
        related_count = len(content_evidence.get("relatedContents", []))
        top_count = len(content_evidence.get("topPerformers", []))
        contrast_count = len(content_evidence.get("contrastContents", []))
        if related_count:
            return f"召回 {related_count} 条当前方向相关内容，并参考 {top_count} 条账号高表现内容，适合先做一条可验证选题。"
        if top_count:
            return f"当前方向相关证据偏少，先借用 {top_count} 条高表现内容的表达结构做小步测试。"
        return f"当前只有 {len(evidence)} 条记忆证据，建议先生成低成本验证题，不直接押重投入。"

    def _fallback_title(
        self,
        direction: str,
        playbook: tuple[str, str],
        index: int,
        related_contents: List[Dict[str, Any]],
        top_performers: List[Dict[str, Any]],
    ) -> str:
        label, _description = playbook
        source = (related_contents or [{}])[index % max(len(related_contents or [{}]), 1)]
        source_title = self._short_text(source.get("title"))
        if source_title:
            return f"{direction}：从《{source_title}》延展一个{label}选题"
        templates = [
            f"{direction}，先拍一个真实场景再讲方法",
            f"{direction}第一条内容该回答什么问题",
            f"{direction}能不能做，先看这笔成本账",
            f"{direction}别急着做路线图，先做一次反例复盘",
        ]
        return templates[index % len(templates)]

    def _fallback_angle(
        self,
        playbook: tuple[str, str],
        related_contents: List[Dict[str, Any]],
        top_performers: List[Dict[str, Any]],
        contrast_contents: List[Dict[str, Any]],
        index: int,
    ) -> str:
        _label, description = playbook
        related = (related_contents or [{}])[index % max(len(related_contents or [{}]), 1)]
        top = (top_performers or [{}])[index % max(len(top_performers or [{}]), 1)]
        contrast = (contrast_contents or [{}])[index % max(len(contrast_contents or [{}]), 1)]
        parts = [description]
        if related.get("title"):
            parts.append(f"当前方向参考《{self._short_text(related.get('title'))}》。")
        if top.get("title"):
            parts.append(f"表达结构参考高表现内容《{self._short_text(top.get('title'))}》。")
        if contrast.get("title"):
            parts.append(f"避开《{self._short_text(contrast.get('title'))}》这类低表现表达。")
        return "".join(parts)

    def _fallback_hook(self, direction: str, playbook: tuple[str, str], related_contents: List[Dict[str, Any]], index: int) -> str:
        label, _description = playbook
        related = (related_contents or [{}])[index % max(len(related_contents or [{}]), 1)]
        if related.get("title"):
            return f"这条不是讲{direction}的大道理，我只拆《{self._short_text(related.get('title'))}》里最值得复拍的一点。"
        return f"{direction}先别做成教程，今天只回答一个具体问题。"

    def _default_tags(self, request: TopicIdeaGenerateRequest) -> List[str]:
        tags = [f"#{request.direction.replace(' ', '')[:12]}", "#内容选题", f"#{request.goal}"]
        if request.platforms:
            tags.append(f"#{request.platforms[0].value}")
        return tags[:4]

    def _short_text(self, value: Any, limit: int = 24) -> str:
        text = str(value or "").strip().replace("\n", " ")
        return text if len(text) <= limit else f"{text[:limit]}..."

    def _style_rules(self, request: TopicIdeaGenerateRequest) -> Dict[str, Any]:
        return {
            "language": "中文",
            "voice": "像内容策划给创作者写选题卡，具体、克制、能直接拍",
            "mustUse": [
                "优先引用 relatedContents/topPerformers/contrastContents 中的标题、指标、评论或关键词",
                "每个 angle 都要说明可拍场景、素材来源或验证方式",
                "risk 必须写具体风险，例如证据不足、表达过泛、平台不适配、素材成本高",
                "recommendReason 必须解释为何现在值得拍，不能只写趋势判断",
            ],
            "avoidPhrases": [
                "普通人自救",
                "先看懂这3条路",
                "底层逻辑",
                "认知升级",
                "时代红利",
                "焦虑不是问题",
                "闭环",
                "赋能",
            ],
            "platforms": [platform.value for platform in request.platforms],
        }

    def _provider_diagnostics(self) -> Dict[str, Any]:
        settings = get_settings()
        diagnostics = {
            "llmProvider": settings.llm_provider,
            "deepseekKeyConfigured": bool(settings.deepseek_api_key),
            "embeddingProvider": settings.embedding_provider,
            "dashscopeKeyConfigured": bool(settings.dashscope_api_key),
        }
        if settings.llm_provider == "mock" and settings.deepseek_api_key:
            diagnostics["providerWarning"] = "deepseek_key_configured_but_provider_mock"
        return diagnostics

    def _progress(self, step: str, message: str) -> str:
        return self._sse_event("progress", {"step": step, "message": message})

    def _evidence_ids(self, evidence: List[Dict[str, Any]]) -> List[str]:
        ids: List[str] = []
        for item in evidence:
            value = item.get("memoryId") or item.get("id")
            if value is not None:
                ids.append(str(value))
        return ids

    def _sse_event(self, event: str, data: Dict[str, Any]) -> str:
        body = json.dumps(data, ensure_ascii=False)
        return f"event: {event}\ndata: {body}\n\n"

    def _candidate_id(self, direction: str, index: int) -> str:
        digest = hashlib.sha1(f"{direction}:{index}".encode("utf-8")).hexdigest()[:10]
        return f"tp_{digest}"

    def _score(self, value: Any, base: int, index: int, descending: bool = True) -> int:
        if isinstance(value, (int, float)):
            return max(0, min(100, round(value)))
        score = base - index if descending else base + index
        return max(0, min(100, score))

    def _system_prompt(self) -> str:
        return (
            "你是 VO Mate 的资深选题策划，不是文案生成器。请只基于输入里的历史内容证据、"
            "账号高表现内容、避坑反例、受众画像、搜索意图和记忆证据生成候选。"
            "每个候选都必须具体到可拍场景、素材来源、验证方式或评论问题；不要写空泛判断、"
            "宏大趋势、鸡汤式标题或 AI 腔套话。标题要像创作者当天能拍的一条内容，"
            "angle/recommendReason/risk 要能解释为什么它贴合这个账号。只返回 JSON。"
        )

    def _candidate_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "required": ["candidates"],
            "properties": {
                "candidates": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["title", "angle", "predictedScore", "seoScore", "audienceScore", "difficultyScore", "risk"],
                    },
                }
            },
        }


topic_idea_service = TopicIdeaGenerationService(topic_idea_repository, topic_evidence_service)
