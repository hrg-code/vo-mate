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
        templates = [
            ("岗位切换", "把焦虑改写成可执行职业策略", "career_growth"),
            ("AI 协作", "用真实任务拆解普通人和 AI 的边界", "ai_collaboration"),
            ("搜索承接", "围绕高频搜索词做清单式解答", "seo_opportunity"),
            ("失败复盘", "反向拆解低效内容为什么不值得继续拍", "retrospective"),
            ("爆款结构", "复用高互动开头和三段式表达", "content_pattern"),
            ("受众问题", "从评论区问题切入给出具体步骤", "audience_need"),
            ("平台差异", "同一主题拆成短视频和图文两种角度", "platform_fit"),
            ("避坑清单", "用风险提醒降低决策成本", "risk_education"),
            ("案例故事", "用一个真实场景承接抽象观点", "storytelling"),
            ("行动路线", "给出 30 天可执行路线图", "conversion_path"),
        ]
        candidates = []
        for index in range(count):
            label, angle_seed, category = templates[index % len(templates)]
            score_base = max(72, 91 - index * 2)
            title = f"{direction}：{label}比单纯努力更重要"
            candidates.append(
                {
                    "title": title,
                    "topic": direction,
                    "angle": f"{angle_seed}，适合 {platforms[0]} 首发并改写到多平台。",
                    "category": category,
                    "targetAudience": audience,
                    "targetPlatforms": platforms,
                    "predictedScore": min(95, score_base + evidence_count),
                    "seoScore": min(95, 84 + (index % 4) * 2),
                    "audienceScore": min(95, 82 + (index % 5) * 2),
                    "difficultyScore": 38 + (index % 6) * 5,
                    "risk": "注意避免泛泛讲道理，必须给出具体案例或步骤。",
                    "recommendReason": f"结合 {evidence_count} 条历史/记忆证据，{label}方向更容易解释清楚并承接后续脚本生成。",
                    "suggestedTitles": [
                        title,
                        f"{direction}别先急着下结论，先看这 3 个信号",
                        f"普通人做{direction}，最该避开的不是起点低",
                    ],
                    "suggestedHooks": [
                        f"如果你正在纠结{direction}，先别急着否定自己。",
                        "真正拉开差距的不是信息量，而是你能不能拆成下一步。",
                    ],
                    "suggestedTags": ["#程序员", "#职业成长", "#AI时代", "#普通人自救"],
                    "nextActions": ["generate_titles", "generate_script", "save_to_topic_pool"],
                }
            )
        return {"candidates": candidates}


class DeepSeekChatProvider(ChatProvider):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def generate_json(self, task: str, system_prompt: str, user_input: str, context: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        if not self.settings.deepseek_api_key:
            return MockChatProvider().generate_json(task, system_prompt, user_input, context, schema)

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

    def get_embedding_provider(self) -> EmbeddingProvider:
        settings = get_settings()
        if settings.embedding_provider == "dashscope":
            return DashScopeEmbeddingProvider(settings)
        return MockEmbeddingProvider(settings.dashscope_embedding_dimension)


ai_provider_service = AIProviderService()
