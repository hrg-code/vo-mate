from __future__ import annotations

from app.agents.runtime.state import ContentCreationState


def route_after_qa(state: ContentCreationState) -> str:
    qa_report = state.get("qa_report", {})
    revision_count = int(state.get("revision_count", 0))
    must_fix = qa_report.get("mustFix", []) if isinstance(qa_report, dict) else []
    if must_fix and revision_count < 1:
        return "revise_content"
    return "finalize_response"

