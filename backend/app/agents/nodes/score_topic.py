from __future__ import annotations

from app.agents.policies.scoring import score_topic as calculate_topic_score
from app.agents.runtime.events import record_step
from app.agents.runtime.state import ContentCreationState


def score_topic(state: ContentCreationState) -> ContentCreationState:
    evidence_count = len(state.get("evidence", []))
    scores = calculate_topic_score(evidence_count)
    record_step(state["run_id"], "score_topic", {"evidenceCount": evidence_count}, scores.model_dump(by_alias=True))
    return {"scores": scores}

