from __future__ import annotations

from typing import Any, TypedDict


class ContentCreationState(TypedDict, total=False):
    run_id: str
    thread_id: str
    workspace_id: str
    member_id: str
    account_id: str

    request: dict[str, Any]
    topic_brief: dict[str, Any]
    account_context: dict[str, Any]

    retrieval_queries: list[dict[str, Any]]
    evidence: list[Any]
    scores: Any

    strategy: dict[str, Any]
    drafts: dict[str, Any]
    qa_report: dict[str, Any]
    revision_count: int

    final_response: Any
    errors: list[dict[str, Any]]

