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


PROMPT_VERSION = "v0.1"


class TopicIdeaGenerationService:
    def __init__(self, topic_repository: TopicIdeaRepository, evidence_service: TopicEvidenceService) -> None:
        self.topic_repository = topic_repository
        self.evidence_service = evidence_service

    def stream_topic_idea_events(self, request: TopicIdeaGenerateRequest) -> Iterator[str]:
        generation_id = f"gen_{uuid4().hex[:10]}"
        provider_name = get_settings().llm_provider
        model_name = get_settings().deepseek_model if provider_name == "deepseek" else None
        try:
            accepted_payload = request.model_dump(by_alias=True, mode="json")
            self.topic_repository.record_generation_started(
                generation_id=generation_id,
                workspace_id=request.workspace_id,
                provider=provider_name,
                model=model_name,
                prompt_version=PROMPT_VERSION,
                input_payload=accepted_payload,
            )
            yield self._sse_event(
                "start",
                {
                    "workflow": "topic-ideas",
                    "generationId": generation_id,
                    "promptVersion": PROMPT_VERSION,
                    "acceptedPayload": accepted_payload,
                },
            )
            yield self._progress("parse_request", "已解析选题方向、平台和目标。")

            workspace_context = self.evidence_service.load_workspace_context(request)
            yield self._progress("load_workspace_context", "已加载工作区和账号上下文。")

            content_metrics = self.evidence_service.load_content_metrics(request)
            yield self._progress("load_content_metrics", "已读取历史内容表现摘要。")

            evidence = self.evidence_service.retrieve_topic_memories(request)
            accepted_payload["dataSourceMode"] = self.evidence_service.data_source_mode
            self.topic_repository.update_generation_input(generation_id, accepted_payload)
            if request.include_evidence:
                yield self._sse_event("evidence", {"items": evidence})
            yield self._progress("retrieve_topic_memories", "已召回相似历史内容和长期记忆。")

            pattern_summary = self._analyze_patterns(content_metrics, evidence)
            yield self._progress("analyze_patterns", "已分析高低表现模式和搜索承接机会。")

            ideas = self.generate_topic_ideas(
                request=request,
                generation_id=generation_id,
                workspace_context=workspace_context,
                content_metrics=content_metrics,
                evidence=evidence,
                pattern_summary=pattern_summary,
            )
            yield self._progress("generate_candidates", f"已生成 {len(ideas)} 个候选选题。")

            ranked_ideas = sorted(ideas, key=lambda idea: idea.predicted_score, reverse=True)
            yield self._progress("score_candidates", "已完成选题评分和优先级排序。")

            self.topic_repository.save_generated_ideas(ranked_ideas, source_payload=accepted_payload)
            yield self._progress("persist_topic_ideas", "已写入选题池边界，等待后续接入真实数据库。")

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
            )
            yield self._sse_event(
                "done",
                output_payload,
            )
        except Exception as exc:
            self.topic_repository.record_generation_failed(generation_id, str(exc))
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
        content_metrics: List[Dict[str, Any]] | None = None,
        evidence: List[Dict[str, Any]] | None = None,
        pattern_summary: Dict[str, Any] | None = None,
    ) -> List[TopicIdea]:
        generation_id = generation_id or f"gen_{uuid4().hex[:10]}"
        workspace_context = workspace_context or self.evidence_service.load_workspace_context(request)
        content_metrics = content_metrics or self.evidence_service.load_content_metrics(request)
        evidence = evidence or self.evidence_service.retrieve_topic_memories(request)
        pattern_summary = pattern_summary or self._analyze_patterns(content_metrics, evidence)

        provider = ai_provider_service.get_chat_provider()
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
                "contentMetrics": content_metrics,
                "evidence": evidence,
                "patternSummary": pattern_summary,
                "dataSourceMode": self.evidence_service.data_source_mode,
            },
            schema=self._candidate_schema(),
        )
        candidates = provider_output.get("candidates", [])
        if not isinstance(candidates, list) or not candidates:
            candidates = self._fallback_candidates(request, evidence)
        return self._coerce_candidates(request, generation_id, candidates, evidence)

    def _coerce_candidates(
        self,
        request: TopicIdeaGenerateRequest,
        generation_id: str,
        candidates: List[Dict[str, Any]],
        evidence: List[Dict[str, Any]],
    ) -> List[TopicIdea]:
        ideas: List[TopicIdea] = []
        source_candidates = candidates[: request.count]
        if len(source_candidates) < request.count:
            source_candidates.extend(self._fallback_candidates(request, evidence)[len(source_candidates) : request.count])

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
                "risk": candidate.get("risk") or "需要补充真实案例，避免泛泛表达。",
                "recommendReason": candidate.get("recommendReason")
                or f"参考 {len(evidence)} 条历史内容和记忆证据后，该方向具备继续拆解价值。",
                "evidenceCount": len(evidence),
                "evidence": visible_evidence,
                "suggestedTitles": candidate.get("suggestedTitles") or [candidate.get("title") or request.direction],
                "suggestedHooks": candidate.get("suggestedHooks") or [f"如果你也在关注{request.direction}，先看这三个信号。"],
                "suggestedTags": candidate.get("suggestedTags") or ["#程序员", "#职业成长", "#AI时代"],
                "nextActions": candidate.get("nextActions") or ["generate_titles", "generate_script", "save_to_topic_pool"],
                "generationId": generation_id,
            }
            try:
                ideas.append(TopicIdea(**data))
            except ValidationError:
                data["targetPlatforms"] = [platform.value for platform in request.platforms] or [Platform.douyin.value]
                ideas.append(TopicIdea(**data))

        return ideas

    def _fallback_candidates(self, request: TopicIdeaGenerateRequest, evidence: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        platforms = [platform.value for platform in request.platforms]
        labels = ["定位", "搜索", "案例", "避坑", "路线", "复盘", "工具", "转型", "人设", "清单"]
        return [
            {
                "title": f"{request.direction}：普通人最该先搞懂的{label}",
                "topic": request.direction,
                "angle": f"用{label}切入，把抽象方向拆成可拍、可执行的 60 秒内容。",
                "category": "fallback_topic",
                "targetAudience": request.audience or "普通创作者的核心受众",
                "targetPlatforms": platforms,
                "predictedScore": max(72, 90 - index * 2),
                "seoScore": max(70, 86 - index),
                "audienceScore": max(70, 84 - index),
                "difficultyScore": 40 + index,
                "risk": "需要加入具体历史案例，避免像泛知识总结。",
                "recommendReason": f"当前召回 {len(evidence)} 条证据，适合先做低成本验证。",
                "suggestedTitles": [f"{request.direction}，先看懂这 3 个{label}"],
                "suggestedHooks": [f"很多人聊{request.direction}，但第一步经常搞反。"],
                "suggestedTags": ["#程序员", "#职业成长", "#内容选题"],
                "nextActions": ["generate_titles", "generate_script", "save_to_topic_pool"],
            }
            for index in range(request.count)
            for label in [labels[index % len(labels)]]
        ]

    def _analyze_patterns(self, content_metrics: List[Dict[str, Any]], evidence: List[Dict[str, Any]]) -> Dict[str, Any]:
        top_content = content_metrics[0] if content_metrics else {}
        return {
            "topContentTitle": top_content.get("title"),
            "topContentScore": top_content.get("score"),
            "evidenceCount": len(evidence),
            "recommendation": "优先选择能承接搜索词、评论问题和账号人设的选题。",
        }

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
            "你是 VO Mate 的选题策略 Agent。请基于历史内容、受众画像、搜索意图和记忆证据，"
            "生成可拍、可解释、可排序的自媒体选题候选，并只返回 JSON。"
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
