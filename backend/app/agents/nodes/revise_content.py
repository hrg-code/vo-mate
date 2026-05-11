from __future__ import annotations

from copy import deepcopy

from app.agents.runtime.events import record_step
from app.agents.runtime.state import ContentCreationState


def revise_content(state: ContentCreationState) -> ContentCreationState:
    drafts = deepcopy(state.get("drafts", {}))
    qa_report = state.get("qa_report", {})
    must_fix = qa_report.get("mustFix", []) if isinstance(qa_report, dict) else []
    if must_fix:
        drafts["revisionNote"] = "已根据质检建议收敛表达：" + "；".join(str(item) for item in must_fix[:2])
    revision_count = int(state.get("revision_count", 0)) + 1
    output = {"drafts": drafts, "revisionCount": revision_count}
    record_step(state["run_id"], "revise_content", {"qaReport": qa_report}, output)
    return {"drafts": drafts, "revision_count": revision_count}

