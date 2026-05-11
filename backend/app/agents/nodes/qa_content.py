from __future__ import annotations

from app.agents.chains.qa_chain import qa_chain
from app.agents.runtime.events import record_step
from app.agents.runtime.state import ContentCreationState


def qa_content(state: ContentCreationState) -> ContentCreationState:
    qa_report = qa_chain.invoke(state.get("drafts", {}), state.get("strategy", {}))
    record_step(state["run_id"], "qa_content", {"drafts": state.get("drafts", {})}, qa_report)
    return {"qa_report": qa_report}

