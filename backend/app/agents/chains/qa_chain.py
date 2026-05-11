from __future__ import annotations

from typing import Any

from app.services.ai_provider_service import ai_provider_service


class QAChain:
    def __init__(self) -> None:
        self.chat_provider = ai_provider_service.get_chat_provider()

    def invoke(self, drafts: dict[str, Any], strategy: dict[str, Any]) -> dict[str, Any]:
        generated = self.chat_provider.generate_json(
            task="qa_content",
            system_prompt="你是内容质检 Agent，请输出 JSON。",
            user_input=str(drafts.get("script", "")),
            context={"drafts": drafts, "strategy": strategy},
            schema={},
        )
        return generated.get("qaReport", {})


qa_chain = QAChain()

