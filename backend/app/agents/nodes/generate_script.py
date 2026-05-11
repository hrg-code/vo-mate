from __future__ import annotations

from app.agents.chains.script_chain import script_chain
from app.agents.runtime.events import record_step
from app.agents.runtime.state import ContentCreationState


def generate_title_description_script(state: ContentCreationState) -> ContentCreationState:
    topic = str(state["request"]["topic"])
    drafts = script_chain.invoke(topic, state.get("strategy", {}))
    record_step(state["run_id"], "generate_title_description_script", {"topic": topic}, drafts)
    return {"drafts": drafts}

