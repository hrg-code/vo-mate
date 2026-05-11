from __future__ import annotations

from typing import Any


class SummaryChain:
    def invoke(self, topic: str, strategy: dict[str, Any]) -> str:
        angle = strategy.get("recommendedAngle", "普通人视角拆解")
        return f"围绕“{topic}”完成选题策略、标题简介脚本生成和质检；推荐角度：{angle}。"


summary_chain = SummaryChain()

