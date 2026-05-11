from __future__ import annotations

from typing import Any

from app.services.ai_provider_service import ai_provider_service


class ScriptChain:
    def __init__(self) -> None:
        self.chat_provider = ai_provider_service.get_chat_provider()

    def invoke(self, topic: str, strategy: dict[str, Any]) -> dict[str, Any]:
        generated = self.chat_provider.generate_json(
            task="generate_title_description_script",
            system_prompt="你是标题、简介和口播脚本生成 Agent，请输出 JSON。",
            user_input=topic,
            context={"topic": topic, "strategy": strategy},
            schema={},
        )
        return generated.get("drafts", {})


script_chain = ScriptChain()

