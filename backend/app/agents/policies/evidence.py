from __future__ import annotations

from typing import Any


def dump_evidence(evidence: list[Any]) -> list[dict[str, Any]]:
    return [item.model_dump(by_alias=True) if hasattr(item, "model_dump") else dict(item) for item in evidence]

