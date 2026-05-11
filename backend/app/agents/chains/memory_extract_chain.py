from __future__ import annotations

from typing import Any


class MemoryExtractChain:
    def invoke(self, final_response: dict[str, Any]) -> dict[str, Any]:
        return {
            "source": "agent_final_response",
            "summary": str(final_response.get("strategy", {}).get("recommendedAngle", "")),
            "status": "candidate",
        }


memory_extract_chain = MemoryExtractChain()

