from __future__ import annotations

from typing import Any

from app.services.ai_provider_service import ai_provider_service


class StrategyChain:
    def __init__(self) -> None:
        self.chat_provider = ai_provider_service.get_chat_provider()

    def invoke(self, topic: str, evidence: list[dict[str, Any]]) -> dict[str, Any]:
        generated = self.chat_provider.generate_json(
            task="generate_strategy",
            system_prompt="你是自媒体工作台的选题策略 Agent，请输出 JSON。",
            user_input=topic,
            context={"topic": topic, "evidence": evidence},
            schema={},
        )
        return generated.get("strategy", {})


strategy_chain = StrategyChain()

