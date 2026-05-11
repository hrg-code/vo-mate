from __future__ import annotations


def get_platform_policy(platform: str) -> dict[str, object]:
    return {"platform": platform, "avoidOverAnxiety": True, "preferActionableAngle": True}

