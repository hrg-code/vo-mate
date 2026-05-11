from __future__ import annotations

from app.schemas.agent import TopicScores


def score_topic(evidence_count: int) -> TopicScores:
    return TopicScores(
        persona_fit=90,
        search_intent_score=84 if evidence_count else 70,
        historical_similarity_score=min(90, 70 + evidence_count * 4),
        retention_potential=76,
        risk_penalty=18,
        topic_score=min(92, 76 + evidence_count * 3),
    )

