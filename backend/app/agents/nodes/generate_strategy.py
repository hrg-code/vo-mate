from __future__ import annotations

from app.agents.chains.strategy_chain import strategy_chain
from app.agents.policies.evidence import dump_evidence
from app.agents.runtime.events import record_step
from app.agents.runtime.state import ContentCreationState


def generate_strategy(state: ContentCreationState) -> ContentCreationState:
    topic = str(state["request"]["topic"])
    strategy = strategy_chain.invoke(topic, dump_evidence(state.get("evidence", [])))
    record_step(state["run_id"], "generate_strategy", {"topic": topic}, strategy)
    return {"strategy": strategy}

