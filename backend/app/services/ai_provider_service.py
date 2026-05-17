from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List

import httpx

from app.core.config import Settings, get_settings


class ChatProvider(ABC):
    @abstractmethod
    def generate_json(self, task: str, system_prompt: str, user_input: str, context: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError


class EmbeddingProvider(ABC):
    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        raise NotImplementedError


class MockChatProvider(ChatProvider):
    def generate_json(self, task: str, system_prompt: str, user_input: str, context: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        if task == "topic_ideas":
            return self._generate_topic_ideas(user_input, context)
        if task == "topic_content_rerank":
            return self._rerank_topic_content(user_input, context)

        topic = context.get("topic") or user_input or "自媒体选题"
        evidence = context.get("evidence", [])
        return {
            "task": task,
            "topic": topic,
            "summary": f"围绕“{topic}”生成一版带证据的内容建议。",
            "strategy": {
                "recommendedAngle": f"用普通人视角拆解“{topic}”的真实问题和可执行路径",
                "targetAudience": ["普通程序员", "转型焦虑人群", "AI 学习者"],
                "risk": "避免过度制造焦虑，标题要给出解决方向。",
            },
            "drafts": {
                "titles": [
                    {"type": "search", "text": f"{topic}，普通人先看懂这 3 条路", "score": 88},
                    {"type": "persona", "text": f"我这种野生程序员怎么看{topic}", "score": 84},
                    {"type": "hook", "text": f"{topic}不是终点，而是一次岗位切换信号", "score": 82},
                ],
                "description": f"一个普通程序员视角，聊聊{topic}背后的真实焦虑、职业选择和 AI 时代的可执行路线。",
                "tags": ["#程序员", "#职业规划", "#AI时代", "#普通人自救"],
                "script": "开头 3 秒：如果你也在担心这个问题，先别急着否定自己。\n主体：真正的问题不是年龄或工具，而是你还停留在只执行需求的岗位形态里。\n转折：普通人要做的是把经验变成可迁移能力。\n结尾：如果你想看具体路线，我下一条拆给你。",
            },
            "qaReport": {
                "personaScore": 90,
                "seoGeoScore": 84,
                "retentionScore": 78,
                "riskScore": 18,
                "conversionScore": 80,
                "mustFix": ["开头可以更快抛出冲突", "简介要自然覆盖核心搜索词"],
            },
            "evidenceUsed": evidence[:3],
        }

    def _generate_topic_ideas(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        direction = user_input or context.get("direction") or "自媒体选题"
        count = int(context.get("count") or 10)
        platforms = context.get("platforms") or ["douyin"]
        audience = context.get("audience") or "目标创作者的核心受众"
        evidence_count = len(context.get("evidence", []))
        content_evidence = context.get("contentEvidence") or {}
        related_contents = content_evidence.get("relatedContents") or []
        top_performers = content_evidence.get("topPerformers") or []
        contrast_contents = content_evidence.get("contrastContents") or []
        pattern_summary = context.get("patternSummary") or {}
        playbooks = [
            ("case_replay", "真实复盘", "拿一条历史内容或真实经历复盘，讲清楚发生了什么、哪里值得复拍。"),
            ("comment_question", "评论问题", "把观众会追问的问题前置，直接回答一个判断标准。"),
            ("search_answer", "搜索承接", "围绕明确搜索词给答案，适合沉淀成图文或短视频合集。"),
            ("avoid_pattern", "避坑反例", "对照低表现内容，指出这个方向最容易拍空的地方。"),
            ("cost_breakdown", "成本账", "把时间、钱、素材和技能门槛拆出来，降低决策成本。"),
            ("first_step", "第一步", "只讲今天能做的一步，方便低成本验证。"),
            ("platform_split", "平台改写", "同一素材拆成短视频开头和图文清单两个版本。"),
            ("script_test", "脚本实验", "设计一个 A/B 钩子实验，先测互动再决定是否扩展。"),
        ]
        candidates = []
        for index in range(count):
            category, label, angle_seed = playbooks[index % len(playbooks)]
            related = self._pick(related_contents, index)
            top = self._pick(top_performers, index)
            contrast = self._pick(contrast_contents, index)
            score_base = max(70, 87 - index * 2 + min(len(related_contents), 4))
            title = self._topic_title(direction, label, index, related, top)
            candidates.append(
                {
                    "title": title,
                    "topic": direction,
                    "angle": self._topic_angle(angle_seed, platforms, related, top, contrast),
                    "category": category,
                    "targetAudience": audience,
                    "targetPlatforms": platforms,
                    "predictedScore": min(95, score_base + evidence_count),
                    "seoScore": min(92, 78 + len(related_contents) * 2 + (index % 3)),
                    "audienceScore": min(92, 80 + evidence_count + (index % 4)),
                    "difficultyScore": 34 + (index % 6) * 4,
                    "risk": self._topic_risk(label, related, contrast),
                    "recommendReason": self._topic_reason(label, related, top, pattern_summary, evidence_count),
                    "suggestedTitles": [
                        title,
                        self._alternate_title(direction, label, index, related),
                        self._alternate_title(direction, "素材清单", index + 1, top),
                    ],
                    "suggestedHooks": [
                        self._topic_hook(direction, label, related),
                        f"这条先不讲大方向，只拆{direction}里最容易被忽略的一个选择。",
                    ],
                    "suggestedTags": self._topic_tags(direction, context, platforms),
                    "nextActions": ["generate_titles", "generate_script", "save_to_topic_pool"],
                }
            )
        return {"candidates": candidates}

    def _pick(self, items: List[Dict[str, Any]], index: int) -> Dict[str, Any]:
        if not items:
            return {}
        return items[index % len(items)]

    def _short_text(self, value: Any, limit: int = 24) -> str:
        text = str(value or "").strip().replace("\n", " ")
        return text if len(text) <= limit else f"{text[:limit]}..."

    def _metric_line(self, item: Dict[str, Any]) -> str:
        if not item:
            return ""
        parts = []
        if item.get("views") is not None:
            parts.append(f"播放 {item['views']}")
        if item.get("comments") is not None:
            parts.append(f"评论 {item['comments']}")
        if item.get("completionRate") is not None:
            parts.append(f"完播 {item['completionRate']}")
        if item.get("score") is not None:
            parts.append(f"评分 {item['score']}")
        return "，".join(parts[:3])

    def _topic_title(self, direction: str, label: str, index: int, related: Dict[str, Any], top: Dict[str, Any]) -> str:
        source_title = self._short_text(related.get("title"))
        if source_title:
            title_by_label = {
                "真实复盘": f"{direction}：把《{source_title}》复拍成一次真实复盘",
                "评论问题": f"{direction}：观众看完《{source_title}》最该追问什么",
                "搜索承接": f"{direction}：用《{source_title}》承接一个具体搜索问题",
                "避坑反例": f"{direction}：为什么《{source_title}》这类表达容易拍空",
                "成本账": f"{direction}：先算清《{source_title}》背后的成本账",
                "第一步": f"{direction}：从《{source_title}》拆出今天能做的第一步",
                "平台改写": f"{direction}：把《{source_title}》改成短视频和图文两版",
                "脚本实验": f"{direction}：拿《{source_title}》做一次开头 A/B 测试",
            }
            return title_by_label.get(label, f"{direction}：从《{source_title}》延展一个新选题")
        templates = [
            f"{direction}第一条内容该回答什么问题",
            f"{direction}能不能做，先看一笔真实成本账",
            f"{direction}别先做教程，先拍一个失败场景",
            f"{direction}今天只验证一个最小动作",
        ]
        return templates[index % len(templates)]

    def _alternate_title(self, direction: str, label: str, index: int, source: Dict[str, Any]) -> str:
        source_title = self._short_text(source.get("title"))
        if source_title:
            return f"复用《{source_title}》的结构，重拍一次{direction}"
        alternatives = [
            f"{direction}先别铺开讲，先拆一个{label}",
            f"{direction}这条内容只解决一个具体问题",
            f"{direction}低成本验证清单",
        ]
        return alternatives[index % len(alternatives)]

    def _topic_angle(
        self,
        angle_seed: str,
        platforms: List[str],
        related: Dict[str, Any],
        top: Dict[str, Any],
        contrast: Dict[str, Any],
    ) -> str:
        parts = [angle_seed]
        if related.get("title"):
            metric_line = self._metric_line(related)
            suffix = f"（{metric_line}）" if metric_line else ""
            parts.append(f"当前方向参考《{self._short_text(related.get('title'))}》{suffix}。")
        if top.get("title"):
            parts.append(f"账号表达结构参考高表现内容《{self._short_text(top.get('title'))}》。")
        if contrast.get("title"):
            parts.append(f"同时避开《{self._short_text(contrast.get('title'))}》这类弱表达。")
        if platforms:
            parts.append(f"先按 {platforms[0]} 的节奏做首发。")
        return "".join(parts)

    def _topic_risk(self, label: str, related: Dict[str, Any], contrast: Dict[str, Any]) -> str:
        if not related:
            return "当前方向相关证据不足，必须先补真实案例或评论问题，否则容易像泛知识总结。"
        if contrast.get("title"):
            return f"不要复用《{self._short_text(contrast.get('title'))}》里的空泛表达，脚本里要保留具体场景和数据。"
        if label in {"搜索承接", "平台改写"}:
            return "标题能承接搜索，但正文不能堆关键词，需要用一个真实问题串起来。"
        return "历史证据只说明值得测试，不代表可以直接做成系列，先用单条内容验证互动。"

    def _topic_reason(
        self,
        label: str,
        related: Dict[str, Any],
        top: Dict[str, Any],
        pattern_summary: Dict[str, Any],
        evidence_count: int,
    ) -> str:
        if related.get("title"):
            metric_line = self._metric_line(related)
            metric_suffix = f"，历史表现为 {metric_line}" if metric_line else ""
            return f"{label}方向可直接绑定《{self._short_text(related.get('title'))}》这条相关证据{metric_suffix}，比重新发明选题更稳。"
        if top.get("title"):
            return f"当前相关证据偏少，但《{self._short_text(top.get('title'))}》是账号高表现内容，可先复用它的开头结构做验证。"
        if pattern_summary.get("topContentTitle"):
            return f"先参考历史高表现内容《{self._short_text(pattern_summary.get('topContentTitle'))}》的表达方式，降低试错成本。"
        return f"只召回 {evidence_count} 条记忆证据，建议先做一条轻量测试，不作为长期系列。"

    def _topic_hook(self, direction: str, label: str, related: Dict[str, Any]) -> str:
        if related.get("title"):
            return f"这条不重新讲{direction}，我只拆《{self._short_text(related.get('title'))}》里最值得复用的一点。"
        if label == "成本账":
            return f"{direction}到底值不值得做，先别听建议，先算这笔账。"
        return f"{direction}先别做成大课，今天只回答一个真实问题。"

    def _topic_tags(self, direction: str, context: Dict[str, Any], platforms: List[str]) -> List[str]:
        tags = [f"#{direction.replace(' ', '')[:12]}", "#内容选题"]
        goal = context.get("goal")
        if goal:
            tags.append(f"#{goal}")
        if platforms:
            tags.append(f"#{platforms[0]}")
        return tags[:4]

    def _rerank_topic_content(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        direction = user_input or context.get("direction") or ""
        terms = [term for term in direction.replace("，", " ").replace("、", " ").split() if term]
        candidates = context.get("candidates", [])
        items = []
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            haystack = " ".join(
                [
                    str(candidate.get("title") or ""),
                    str(candidate.get("description") or ""),
                    " ".join(candidate.get("tags") or []),
                    " ".join(candidate.get("keywords") or []),
                    " ".join(candidate.get("matchedTerms") or []),
                ]
            )
            overlap = sum(1 for term in terms if term in haystack)
            if overlap >= 2:
                level = "same_topic"
                score = 0.9
            elif overlap == 1 or candidate.get("ruleRelevanceLevel") in {"strong_related", "medium_related"}:
                level = "adjacent_topic"
                score = 0.76
            else:
                level = "weak"
                score = 0.42
            items.append(
                {
                    "contentId": candidate.get("contentId"),
                    "relevanceLevel": level,
                    "score": score,
                    "reason": f"Mock rerank 根据方向“{direction}”和候选命中词判断为 {level}。",
                    "suggestedUse": "用于当前方向证据" if level in {"same_topic", "adjacent_topic"} else "不作为当前方向证据",
                }
            )
        return {"items": items}


class DeepSeekChatProvider(ChatProvider):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def generate_json(self, task: str, system_prompt: str, user_input: str, context: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        if not self.settings.deepseek_api_key:
            raise RuntimeError("VO_MATE_DEEPSEEK_API_KEY is required for DeepSeek chat provider")
        payload = {
            "model": self.settings.deepseek_model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": json.dumps(
                        {"task": task, "input": user_input, "context": context, "schema": schema},
                        ensure_ascii=False,
                    ),
                },
            ],
        }

        with httpx.Client(timeout=self.settings.deepseek_timeout_seconds) as client:
            response = client.post(
                f"{self.settings.deepseek_base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {self.settings.deepseek_api_key}", "Content-Type": "application/json"},
                json=payload,
            )
            response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return json.loads(content)


class MockEmbeddingProvider(EmbeddingProvider):
    def __init__(self, dimension: int = 1024) -> None:
        self.dimension = dimension

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed(text)

    def _embed(self, text: str) -> List[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values: List[float] = []
        for index in range(self.dimension):
            byte = digest[index % len(digest)]
            values.append((byte / 255.0) - 0.5)
        return values


class DashScopeEmbeddingProvider(EmbeddingProvider):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.mock = MockEmbeddingProvider(settings.dashscope_embedding_dimension)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._embed(texts, text_type="document")

    def embed_query(self, text: str) -> List[float]:
        return self._embed([text], text_type="query")[0]

    def _embed(self, texts: List[str], text_type: str) -> List[List[float]]:
        if not self.settings.dashscope_api_key:
            return self.mock.embed_documents(texts)

        payload = {
            "model": self.settings.dashscope_embedding_model,
            "input": {"texts": texts},
            "parameters": {
                "text_type": text_type,
                "dimension": self.settings.dashscope_embedding_dimension,
            },
        }
        with httpx.Client(timeout=self.settings.connection_timeout_seconds) as client:
            response = client.post(
                f"{self.settings.dashscope_base_url.rstrip('/')}/services/embeddings/text-embedding/text-embedding",
                headers={"Authorization": f"Bearer {self.settings.dashscope_api_key}", "Content-Type": "application/json"},
                json=payload,
            )
            response.raise_for_status()
        embeddings = [item["embedding"] for item in response.json()["output"]["embeddings"]]
        for embedding in embeddings:
            if len(embedding) != self.settings.dashscope_embedding_dimension:
                raise ValueError("DashScope embedding dimension mismatch")
        return embeddings


class AIProviderService:
    def get_chat_provider(self) -> ChatProvider:
        settings = get_settings()
        if settings.llm_provider == "deepseek":
            return DeepSeekChatProvider(settings)
        return MockChatProvider()

    def get_required_chat_provider(self) -> ChatProvider:
        settings = get_settings()
        if settings.llm_provider != "deepseek":
            raise RuntimeError("VO_MATE_LLM_PROVIDER must be deepseek for real topic idea generation")
        if not settings.deepseek_api_key:
            raise RuntimeError("VO_MATE_DEEPSEEK_API_KEY is required for real topic idea generation")
        return DeepSeekChatProvider(settings)

    def get_embedding_provider(self) -> EmbeddingProvider:
        settings = get_settings()
        if settings.embedding_provider == "dashscope":
            return DashScopeEmbeddingProvider(settings)
        return MockEmbeddingProvider(settings.dashscope_embedding_dimension)


ai_provider_service = AIProviderService()
