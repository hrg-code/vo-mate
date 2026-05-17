from __future__ import annotations

from typing import Any, Dict, List

from app.core.config import get_settings
from app.schemas.common import TopicIdeaGenerateRequest
from app.services.ai_provider_service import ai_provider_service


ACCEPTED_RERANK_LEVELS = {"same_topic", "adjacent_topic"}
VALID_RERANK_LEVELS = ACCEPTED_RERANK_LEVELS | {"weak", "unrelated"}


class TopicContentRerankService:
    def rerank(self, request: TopicIdeaGenerateRequest, candidates: List[Dict[str, Any]], max_candidates: int = 24) -> Dict[str, Any]:
        limited_candidates = candidates[:max_candidates]
        diagnostics = {
            "rerankEnabled": True,
            "rerankProvider": get_settings().llm_provider,
            "rerankCandidateCount": len(limited_candidates),
            "rerankAcceptedCount": len(limited_candidates),
            "rerankRejectedCount": 0,
            "rerankFallback": False,
        }
        if not limited_candidates:
            return {"candidates": [], "diagnostics": diagnostics}

        try:
            provider = ai_provider_service.get_required_chat_provider()
            output = provider.generate_json(
                task="topic_content_rerank",
                system_prompt=self._system_prompt(),
                user_input=request.direction,
                context={
                    "direction": request.direction,
                    "goal": request.goal,
                    "audience": request.audience,
                    "constraints": request.constraints,
                    "candidates": [self._candidate_payload(candidate) for candidate in limited_candidates],
                },
                schema=self._schema(),
            )
            items = output.get("items")
            if not isinstance(items, list) or not items:
                return self._fallback(limited_candidates, diagnostics, "empty_rerank_items")

            rerank_by_id = {}
            for item in items:
                if not isinstance(item, dict):
                    continue
                content_id = str(item.get("contentId") or item.get("content_id") or "")
                level = str(item.get("relevanceLevel") or "")
                if not content_id or level not in VALID_RERANK_LEVELS:
                    continue
                rerank_by_id[content_id] = {
                    "llmRelevanceLevel": level,
                    "llmRelevanceScore": self._score(item.get("score")),
                    "llmReason": str(item.get("reason") or ""),
                    "suggestedUse": str(item.get("suggestedUse") or ""),
                }

            if not rerank_by_id:
                return self._fallback(limited_candidates, diagnostics, "invalid_rerank_items")

            accepted: List[Dict[str, Any]] = []
            rejected_count = 0
            for candidate in limited_candidates:
                rerank = rerank_by_id.get(str(candidate.get("contentId")))
                if rerank is None:
                    rejected_count += 1
                    continue
                if rerank["llmRelevanceLevel"] not in ACCEPTED_RERANK_LEVELS:
                    rejected_count += 1
                    continue
                accepted.append({**candidate, **rerank})

            accepted.sort(key=self._sort_key, reverse=True)
            diagnostics["rerankAcceptedCount"] = len(accepted)
            diagnostics["rerankRejectedCount"] = rejected_count
            return {"candidates": accepted, "diagnostics": diagnostics}
        except Exception as exc:
            return self._fallback(limited_candidates, diagnostics, f"{exc.__class__.__name__}: {exc}")

    def _candidate_payload(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "contentId": candidate.get("contentId"),
            "title": candidate.get("title"),
            "description": candidate.get("description"),
            "tags": candidate.get("tags", []),
            "keywords": candidate.get("keywords", []),
            "matchedTerms": candidate.get("matchedTerms", []),
            "matchFields": candidate.get("matchFields", []),
            "ruleRelevanceLevel": candidate.get("relevanceLevel"),
            "ruleRelevanceScore": candidate.get("relevanceScore"),
            "retrievalSource": candidate.get("retrievalSource"),
            "embeddingScore": candidate.get("embeddingScore"),
            "score": candidate.get("score"),
            "views": candidate.get("views"),
        }

    def _fallback(self, candidates: List[Dict[str, Any]], diagnostics: Dict[str, Any], error: str) -> Dict[str, Any]:
        fallback_diagnostics = {
            **diagnostics,
            "rerankAcceptedCount": len(candidates),
            "rerankRejectedCount": 0,
            "rerankFallback": True,
            "rerankSkipped": True,
            "rerankError": error,
        }
        return {"candidates": candidates, "diagnostics": fallback_diagnostics}

    def _score(self, value: Any) -> float:
        if isinstance(value, (int, float)):
            score = float(value)
            if score > 1:
                score = score / 100
            return round(max(0.0, min(1.0, score)), 4)
        return 0.0

    def _sort_key(self, candidate: Dict[str, Any]):
        level_rank = {"same_topic": 2, "adjacent_topic": 1}.get(candidate.get("llmRelevanceLevel"), 0)
        return (
            level_rank,
            candidate.get("llmRelevanceScore") or 0,
            candidate.get("relevanceScore") or 0,
            candidate.get("score") or 0,
            candidate.get("views") or 0,
            candidate.get("publishedAt") or "",
        )

    def _system_prompt(self) -> str:
        return (
            "你是 VO Mate 的内容证据相关性复核器。请判断候选历史内容与当前选题方向的关系，"
            "只返回 JSON。same_topic/adjacent_topic 可用于当前选题生成，weak/unrelated 不应作为当前方向证据。"
        )

    def _schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "required": ["items"],
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["contentId", "relevanceLevel", "score", "reason", "suggestedUse"],
                    },
                }
            },
        }


topic_content_rerank_service = TopicContentRerankService()
