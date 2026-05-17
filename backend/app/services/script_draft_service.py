from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.core.config import get_settings
from app.repositories.script_draft_repository import ScriptDraftRepository, script_draft_repository
from app.schemas.common import ScriptBlockRole, ScriptDraftCreateRequest, ScriptVersionSourceType, ScriptVersionStatus
from app.services.ai_provider_service import ai_provider_service


PROMPT_VERSION = "v0.1"


class ScriptDraftService:
    def __init__(self, draft_repository: ScriptDraftRepository) -> None:
        self.draft_repository = draft_repository

    def create_ai_initial_draft(self, request: ScriptDraftCreateRequest) -> Dict[str, Any]:
        topic = request.topic.strip()
        existing = self.draft_repository.find_draft_for_topic(request.workspace_id, request.topic_idea_id, topic)
        if existing is not None:
            return existing

        draft_id = f"scr_{uuid4().hex[:10]}"
        version_id = f"sv_{uuid4().hex[:10]}"
        generation_id = f"gen_{uuid4().hex[:10]}"
        settings = get_settings()
        provider_name = settings.llm_provider
        model_name = settings.deepseek_model if provider_name == "deepseek" else None
        input_payload = request.model_dump(by_alias=True, mode="json")

        try:
            self.draft_repository.record_generation_started(
                generation_id=generation_id,
                workspace_id=request.workspace_id,
                provider=provider_name,
                model=model_name,
                prompt_version=PROMPT_VERSION,
                input_payload=input_payload,
            )
            generated = ai_provider_service.get_chat_provider().generate_json(
                task="script",
                system_prompt="你是短视频口播脚本生成 Agent，请输出标题候选、简介、标签和脚本文本 JSON。",
                user_input=topic,
                context={
                    "topic": topic,
                    "platform": request.platform.value,
                    "durationSeconds": request.duration_seconds,
                    "topicIdeaId": request.topic_idea_id,
                },
                schema={},
            )
            drafts = self._normalize_drafts(generated, request)
            blocks = drafts["blocks"]
            body = drafts["script"]
            title_candidates = self._title_candidates(drafts.get("titles"))
            draft = {
                "id": draft_id,
                "workspaceId": request.workspace_id,
                "topicIdeaId": request.topic_idea_id,
                "topic": topic,
                "title": request.title or self._first_title(title_candidates) or topic,
                "body": body,
                "platform": request.platform.value,
                "status": "draft",
                "currentVersionId": version_id,
                "adoptedVersionId": None,
            }
            version = {
                "id": version_id,
                "draftId": draft_id,
                "versionNo": 1,
                "label": "v1 AI 初稿",
                "platform": request.platform.value,
                "durationSeconds": request.duration_seconds,
                "body": body,
                "blocks": blocks,
                "description": drafts.get("description"),
                "tags": [str(tag) for tag in drafts.get("tags", [])],
                "titleCandidates": title_candidates,
                "sourceType": ScriptVersionSourceType.ai_initial.value,
                "parentVersionId": None,
                "generationId": generation_id,
                "status": ScriptVersionStatus.candidate.value,
            }
            created = self.draft_repository.create_draft_with_initial_version(
                draft=draft,
                version=version,
                generation_id=generation_id,
                generated=generated,
            )
            self.draft_repository.record_generation_succeeded(
                generation_id,
                output_payload={"draftId": draft_id, "versionId": version_id, "drafts": drafts},
            )
            return created
        except Exception as exc:
            self.draft_repository.record_generation_failed(generation_id, str(exc))
            raise

    def _normalize_drafts(self, generated: Dict[str, Any], request: ScriptDraftCreateRequest) -> Dict[str, Any]:
        raw_drafts = generated.get("drafts")
        drafts = raw_drafts if isinstance(raw_drafts, dict) else {}
        raw_blocks = drafts.get("blocks") or generated.get("blocks") or generated.get("scriptBlocks") or generated.get("script_blocks")
        blocks = self._normalize_blocks(raw_blocks, request.duration_seconds)
        script = self._first_text(
            drafts,
            generated,
            keys=["script", "body", "content", "text", "scriptBody", "script_body"],
        )
        if not script and blocks:
            script = self._compose_body(blocks)
        if not script:
            script = self._fallback_script(request)
        if not blocks:
            blocks = self._blocks_from_body(script, request.duration_seconds)
        return {
            **drafts,
            "script": script,
            "blocks": blocks,
            "titles": drafts.get("titles") or generated.get("titles") or generated.get("titleCandidates") or [],
            "description": drafts.get("description") or generated.get("description"),
            "tags": drafts.get("tags") or generated.get("tags") or [],
        }

    def _first_text(self, *sources: Dict[str, Any], keys: List[str]) -> str:
        for source in sources:
            for key in keys:
                value = source.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
        return ""

    def _fallback_script(self, request: ScriptDraftCreateRequest) -> str:
        topic = request.topic.strip()
        return (
            f"开头 3 秒：如果你正在关注{topic}，先抓住这个关键判断。\n\n"
            "主体：问题不是信息不够，而是缺少一条能执行的路径。先拆清现状，再给出具体动作。\n\n"
            "结尾 CTA：如果你想看下一步怎么做，我下一条继续拆。"
        )

    def _normalize_blocks(self, raw: Any, duration_seconds: int) -> List[Dict[str, Any]]:
        if not isinstance(raw, list):
            return []
        blocks: List[Dict[str, Any]] = []
        for index, item in enumerate(raw):
            if not isinstance(item, dict):
                continue
            voiceover = str(item.get("voiceover") or item.get("text") or item.get("body") or "").strip()
            if not voiceover:
                continue
            role = self._coerce_role(str(item.get("role") or ""), index)
            duration = item.get("durationSeconds") or item.get("duration_seconds")
            blocks.append(
                {
                    "id": str(item.get("id") or f"sb_{role}_{uuid4().hex[:8]}"),
                    "role": role,
                    "label": str(item.get("label") or self._role_label(role)),
                    "voiceover": voiceover,
                    "visualHint": item.get("visualHint") or item.get("visual_hint") or self._visual_hint(role),
                    "startSeconds": item.get("startSeconds") or item.get("start_seconds"),
                    "endSeconds": item.get("endSeconds") or item.get("end_seconds"),
                    "durationSeconds": duration,
                }
            )
        return self._fill_block_durations(blocks, duration_seconds)

    def _blocks_from_body(self, body: str, duration_seconds: int) -> List[Dict[str, Any]]:
        segments = self._body_segments(body)
        durations = self._split_duration(duration_seconds, len(segments))
        blocks: List[Dict[str, Any]] = []
        for index, segment in enumerate(segments):
            role = self._infer_role(segment, index)
            blocks.append(
                {
                    "id": f"sb_{role}_{uuid4().hex[:8]}",
                    "role": role,
                    "label": self._role_label(role),
                    "voiceover": self._strip_section_heading(segment),
                    "visualHint": self._visual_hint(role),
                    "durationSeconds": durations[index] if index < len(durations) else None,
                }
            )
        return blocks

    def _body_segments(self, body: str) -> List[str]:
        normalized = body.strip()
        if not normalized:
            return []
        double_newline_segments = [segment.strip() for segment in normalized.split("\n\n") if segment.strip()]
        if len(double_newline_segments) > 1:
            return double_newline_segments
        heading_pattern = re.compile(r"(?=^(?:开头|前\s*3\s*秒|主体|观点|核心|痛点|案例|证据|方法|步骤|路线|转折|反转|总结|结尾|CTA|互动)[^\\n]{0,20}[：:])", re.M)
        heading_segments = [segment.strip() for segment in heading_pattern.split(normalized) if segment.strip()]
        return heading_segments or [normalized]

    def _compose_body(self, blocks: List[Dict[str, Any]]) -> str:
        parts = []
        for block in blocks:
            voiceover = str(block.get("voiceover") or "").strip()
            if voiceover:
                parts.append(f"{block.get('label') or self._role_label(str(block.get('role') or 'point'))}：\n{voiceover}")
        return "\n\n".join(parts)

    def _fill_block_durations(self, blocks: List[Dict[str, Any]], duration_seconds: int) -> List[Dict[str, Any]]:
        missing_indexes = [index for index, block in enumerate(blocks) if block.get("durationSeconds") is None]
        durations = self._split_duration(duration_seconds, len(blocks))
        for index in missing_indexes:
            if index < len(durations):
                blocks[index]["durationSeconds"] = durations[index]
        return blocks

    def _split_duration(self, duration_seconds: int, count: int) -> List[int]:
        if duration_seconds <= 0 or count <= 0:
            return []
        base = max(3, duration_seconds // count)
        durations = [base for _ in range(count)]
        durations[-1] += max(0, duration_seconds - base * count)
        return durations

    def _infer_role(self, segment: str, index: int) -> str:
        heading = segment.split("\n", 1)[0]
        if self._matches(heading, ["开头", "钩子", "前 3 秒", "hook"]):
            return ScriptBlockRole.hook.value
        if self._matches(heading, ["痛点", "共鸣", "问题"]):
            return ScriptBlockRole.pain.value
        if self._matches(heading, ["主体", "观点", "判断", "核心"]):
            return ScriptBlockRole.point.value
        if self._matches(heading, ["案例", "证据", "经历", "数据"]):
            return ScriptBlockRole.proof.value
        if self._matches(heading, ["方法", "步骤", "路线", "路径"]):
            return ScriptBlockRole.method.value
        if self._matches(heading, ["转折", "反转", "冲突"]):
            return ScriptBlockRole.turn.value
        if self._matches(heading, ["总结", "收束"]):
            return ScriptBlockRole.summary.value
        if self._matches(heading, ["结尾", "CTA", "互动", "关注", "评论"]):
            return ScriptBlockRole.cta.value
        fallback_roles = [
            ScriptBlockRole.hook.value,
            ScriptBlockRole.point.value,
            ScriptBlockRole.turn.value,
            ScriptBlockRole.cta.value,
            ScriptBlockRole.pain.value,
            ScriptBlockRole.proof.value,
            ScriptBlockRole.method.value,
            ScriptBlockRole.summary.value,
        ]
        return fallback_roles[index] if index < len(fallback_roles) else ScriptBlockRole.point.value

    def _coerce_role(self, value: str, index: int) -> str:
        try:
            return ScriptBlockRole(value).value
        except ValueError:
            return self._infer_role(value, index)

    def _strip_section_heading(self, segment: str) -> str:
        lines = segment.split("\n")
        if len(lines) <= 1:
            text = segment.strip()
            for separator in ("：", ":"):
                if separator in text and len(text.split(separator, 1)[0]) <= 18:
                    return text.split(separator, 1)[1].strip()
            return text
        first_line = lines[0].strip()
        if (first_line.endswith("：") or first_line.endswith(":")) and len(first_line) <= 18:
            return "\n".join(lines[1:]).strip()
        for separator in ("：", ":"):
            if separator in first_line and len(first_line.split(separator, 1)[0]) <= 18:
                remainder = first_line.split(separator, 1)[1].strip()
                rest = "\n".join(lines[1:]).strip()
                return "\n".join(part for part in [remainder, rest] if part).strip()
        return segment.strip()

    def _matches(self, value: str, keywords: List[str]) -> bool:
        lower_value = value.lower()
        return any(keyword.lower() in lower_value for keyword in keywords)

    def _role_label(self, role: str) -> str:
        return {
            "hook": "开头钩子",
            "pain": "痛点共鸣",
            "point": "核心观点",
            "proof": "案例/证据",
            "method": "方法论",
            "turn": "反转冲突",
            "summary": "总结",
            "cta": "互动引导",
        }.get(role, "核心观点")

    def _visual_hint(self, role: str) -> str:
        return {
            "hook": "正面半身，第一句直接看镜头。",
            "pain": "切到评论/搜索词截图或表情特写。",
            "point": "稳定口播，屏幕打出核心判断。",
            "proof": "补充历史案例、数据截图或经历画面。",
            "method": "用 2-3 个字幕条拆步骤。",
            "turn": "语速放慢，强调反常识判断。",
            "summary": "回到正面口播，压缩成一句话。",
            "cta": "看镜头，给出评论或下一条承诺。",
        }.get(role, "稳定口播，屏幕打出核心判断。")

    def _title_candidates(self, raw: Any) -> List[Dict[str, Any]]:
        candidates: List[Dict[str, Any]] = []
        if not isinstance(raw, list):
            return candidates
        for item in raw:
            if isinstance(item, dict):
                candidates.append(item)
            else:
                candidates.append({"text": str(item)})
        return candidates

    def _first_title(self, candidates: List[Dict[str, Any]]) -> Optional[str]:
        for candidate in candidates:
            text = candidate.get("text")
            if text:
                return str(text)
        return None


script_draft_service = ScriptDraftService(script_draft_repository)
