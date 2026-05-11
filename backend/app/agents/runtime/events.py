from __future__ import annotations

from typing import Any

from app.services.agent_store_service import agent_store


def slim(payload: dict[str, Any]) -> dict[str, Any]:
    text = str(payload)
    if len(text) <= 2500:
        return payload
    return {"summary": text[:2500], "truncated": True}


def record_step(run_id: str, node_name: str, input_snapshot: dict[str, Any], output_snapshot: dict[str, Any]) -> None:
    agent_store.add_step(run_id, node_name, slim(input_snapshot), slim(output_snapshot))

