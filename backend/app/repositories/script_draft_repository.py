from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import AIGeneration as AIGenerationModel
from app.db.models import ScriptDraft as ScriptDraftModel
from app.db.models import ScriptDraftVersion as ScriptDraftVersionModel
from app.db.session import get_admin_engine
from app.repositories.topic_idea_repository import topic_idea_repository
from app.schemas.common import (
    ScriptCurrentVersionUpdateRequest,
    ScriptDraftCreateRequest,
    ScriptDraftVersionCreateRequest,
    ScriptVersionSourceType,
    ScriptVersionStatus,
)
from app.services.ai_provider_service import ai_provider_service


PROMPT_VERSION = "v0.1"


class ScriptDraftRepository:
    def __init__(self) -> None:
        self.memory_drafts: Dict[str, Dict[str, Any]] = {}
        self.memory_versions: Dict[str, List[Dict[str, Any]]] = {}

    def list_drafts(self) -> List[Dict[str, Any]]:
        with self._session() as session:
            if session is not None:
                try:
                    rows = session.query(ScriptDraftModel).order_by(ScriptDraftModel.updated_at.desc()).limit(100).all()
                    return [self._draft_dict(row, self._current_version(session, row)) for row in rows]
                except SQLAlchemyError:
                    session.rollback()
        return [self._draft_with_current(draft) for draft in self.memory_drafts.values()]

    def get_draft(self, draft_id: str) -> Optional[Dict[str, Any]]:
        with self._session() as session:
            if session is not None:
                try:
                    row = session.get(ScriptDraftModel, draft_id)
                    if row is None:
                        return None
                    versions = (
                        session.query(ScriptDraftVersionModel)
                        .filter(ScriptDraftVersionModel.draft_id == draft_id)
                        .order_by(ScriptDraftVersionModel.version_no.asc())
                        .all()
                    )
                    payload = self._draft_dict(row, self._current_version(session, row))
                    payload["versions"] = [self._version_dict(version) for version in versions]
                    return payload
                except SQLAlchemyError:
                    session.rollback()

        draft = self.memory_drafts.get(draft_id)
        if draft is None:
            return None
        payload = self._draft_with_current(draft)
        payload["versions"] = list(self.memory_versions.get(draft_id, []))
        return payload

    def create_draft(self, request: ScriptDraftCreateRequest) -> Dict[str, Any]:
        draft_id = f"scr_{uuid4().hex[:10]}"
        version_id = f"sv_{uuid4().hex[:10]}"
        generation_id = f"gen_{uuid4().hex[:10]}"
        provider_name = get_settings().llm_provider
        model_name = get_settings().deepseek_model if provider_name == "deepseek" else None
        input_payload = request.model_dump(by_alias=True, mode="json")
        try:
            self._record_generation_started(generation_id, request.workspace_id, provider_name, model_name, input_payload)
            generated = ai_provider_service.get_chat_provider().generate_json(
                task="script",
                system_prompt="你是短视频口播脚本生成 Agent，请输出标题候选、简介、标签和脚本文本 JSON。",
                user_input=request.topic,
                context={
                    "topic": request.topic,
                    "platform": request.platform.value,
                    "durationSeconds": request.duration_seconds,
                    "topicIdeaId": request.topic_idea_id,
                },
                schema={},
            )
            drafts = self._normalize_drafts(generated, request)
            body = drafts["script"]
            title_candidates = self._title_candidates(drafts.get("titles"))
            title = request.title or self._first_title(title_candidates) or request.topic
            description = drafts.get("description")
            tags = [str(tag) for tag in drafts.get("tags", [])]
            draft = {
                "id": draft_id,
                "workspaceId": request.workspace_id,
                "topicIdeaId": request.topic_idea_id,
                "title": title,
                "body": body,
                "platform": request.platform.value,
                "status": "draft",
                "currentVersionId": version_id,
                "adoptedVersionId": None,
                "updatedAt": self._now(),
            }
            version = {
                "id": version_id,
                "draftId": draft_id,
                "versionNo": 1,
                "label": "v1 AI 初稿",
                "platform": request.platform.value,
                "durationSeconds": request.duration_seconds,
                "body": body,
                "description": description,
                "tags": tags,
                "titleCandidates": title_candidates,
                "sourceType": ScriptVersionSourceType.ai_initial.value,
                "parentVersionId": None,
                "generationId": generation_id,
                "status": ScriptVersionStatus.candidate.value,
                "createdAt": self._now(),
            }
            self._persist_created(draft, version, generation_id, generated)
            self._record_generation_succeeded(
                generation_id,
                output_payload={"draftId": draft_id, "versionId": version_id, "drafts": drafts},
            )
            return self.get_draft(draft_id) or {**draft, "currentVersion": version, "versions": [version]}
        except Exception as exc:
            self._record_generation_failed(generation_id, str(exc))
            raise

    def create_version(self, draft_id: str, request: ScriptDraftVersionCreateRequest) -> Optional[Dict[str, Any]]:
        draft = self.get_draft(draft_id)
        if draft is None:
            return None
        versions = draft.get("versions", [])
        version_no = max([version["versionNo"] for version in versions], default=0) + 1
        parent_version_id = request.parent_version_id or draft.get("currentVersionId")
        version_id = f"sv_{uuid4().hex[:10]}"
        label = request.label or f"v{version_no} 用户修改"
        platform = request.platform.value if request.platform is not None else draft.get("platform")
        version = {
            "id": version_id,
            "draftId": draft_id,
            "versionNo": version_no,
            "label": label,
            "platform": platform,
            "durationSeconds": request.duration_seconds,
            "body": request.body,
            "description": request.description,
            "tags": request.tags,
            "titleCandidates": request.title_candidates,
            "sourceType": request.source_type.value,
            "parentVersionId": parent_version_id,
            "generationId": None,
            "status": ScriptVersionStatus.candidate.value,
            "createdAt": self._now(),
        }
        with self._session() as session:
            if session is not None:
                try:
                    row = session.get(ScriptDraftModel, draft_id)
                    if row is None:
                        return None
                    session.merge(self._version_model(version))
                    row.current_version_id = version_id
                    row.body = request.body
                    row.platform = platform
                    session.commit()
                    return self.get_draft(draft_id)
                except SQLAlchemyError:
                    session.rollback()

        self.memory_versions.setdefault(draft_id, []).append(version)
        memory_draft = self.memory_drafts[draft_id]
        memory_draft.update({"currentVersionId": version_id, "body": request.body, "platform": platform, "updatedAt": self._now()})
        return self.get_draft(draft_id)

    def update_version_status(self, draft_id: str, version_id: str, status: ScriptVersionStatus) -> Optional[Dict[str, Any]]:
        draft = self.get_draft(draft_id)
        if draft is None or not any(version["id"] == version_id for version in draft.get("versions", [])):
            return None

        with self._session() as session:
            if session is not None:
                try:
                    draft_row = session.get(ScriptDraftModel, draft_id)
                    version_row = session.get(ScriptDraftVersionModel, version_id)
                    if draft_row is None or version_row is None or version_row.draft_id != draft_id:
                        return None
                    version_row.status = status.value
                    if status == ScriptVersionStatus.adopted:
                        draft_row.adopted_version_id = version_id
                    session.commit()
                    return self.get_draft(draft_id)
                except SQLAlchemyError:
                    session.rollback()

        for version in self.memory_versions.get(draft_id, []):
            if version["id"] == version_id:
                version["status"] = status.value
        if status == ScriptVersionStatus.adopted:
            self.memory_drafts[draft_id]["adoptedVersionId"] = version_id
        return self.get_draft(draft_id)

    def update_current_version(self, draft_id: str, request: ScriptCurrentVersionUpdateRequest) -> Optional[Dict[str, Any]]:
        draft = self.get_draft(draft_id)
        if draft is None:
            return None
        target = next((version for version in draft.get("versions", []) if version["id"] == request.version_id), None)
        if target is None:
            return None

        with self._session() as session:
            if session is not None:
                try:
                    draft_row = session.get(ScriptDraftModel, draft_id)
                    if draft_row is None:
                        return None
                    draft_row.current_version_id = request.version_id
                    draft_row.body = target["body"]
                    draft_row.platform = target.get("platform")
                    session.commit()
                    return self.get_draft(draft_id)
                except SQLAlchemyError:
                    session.rollback()

        self.memory_drafts[draft_id].update(
            {
                "currentVersionId": request.version_id,
                "body": target["body"],
                "platform": target.get("platform"),
                "updatedAt": self._now(),
            }
        )
        return self.get_draft(draft_id)

    def _persist_created(self, draft: Dict[str, Any], version: Dict[str, Any], generation_id: str, generated: Dict[str, Any]) -> None:
        with self._session() as session:
            if session is not None:
                try:
                    session.merge(self._draft_model(draft))
                    session.merge(self._version_model(version))
                    session.commit()
                    return
                except SQLAlchemyError:
                    session.rollback()

        self.memory_drafts[draft["id"]] = draft
        self.memory_versions[draft["id"]] = [version]
        memory_generation = topic_idea_repository.memory_generations.get(generation_id)
        if memory_generation is not None:
            memory_generation["outputPayload"] = {"draftId": draft["id"], "versionId": version["id"], "generated": generated}

    def _record_generation_started(
        self,
        generation_id: str,
        workspace_id: str,
        provider: str,
        model: Optional[str],
        input_payload: Dict[str, Any],
    ) -> None:
        record = {
            "id": generation_id,
            "workspaceId": workspace_id,
            "workflow": "script",
            "provider": provider,
            "model": model,
            "promptVersion": PROMPT_VERSION,
            "inputPayload": input_payload,
            "evidenceIds": [],
            "outputPayload": None,
            "error": None,
            "status": "running",
        }
        with self._session() as session:
            if session is not None:
                try:
                    session.merge(self._generation_model(record))
                    session.commit()
                    return
                except SQLAlchemyError:
                    session.rollback()
        topic_idea_repository.memory_generations[generation_id] = record

    def _record_generation_succeeded(self, generation_id: str, output_payload: Dict[str, Any]) -> None:
        self._finish_generation(generation_id, "succeeded", output_payload, None)

    def _record_generation_failed(self, generation_id: str, error: str) -> None:
        self._finish_generation(generation_id, "failed", None, error)

    def _finish_generation(
        self,
        generation_id: str,
        status: str,
        output_payload: Optional[Dict[str, Any]],
        error: Optional[str],
    ) -> None:
        with self._session() as session:
            if session is not None:
                try:
                    row = session.get(AIGenerationModel, generation_id)
                    if row is not None:
                        row.status = status
                        row.output_payload = output_payload
                        row.error = error
                        session.commit()
                        return
                except SQLAlchemyError:
                    session.rollback()

        record = topic_idea_repository.memory_generations.get(generation_id)
        if record is not None:
            record.update({"status": status, "outputPayload": output_payload, "error": error})

    def _draft_with_current(self, draft: Dict[str, Any]) -> Dict[str, Any]:
        versions = self.memory_versions.get(draft["id"], [])
        current_version = next((version for version in versions if version["id"] == draft.get("currentVersionId")), None)
        return {**draft, "currentVersion": current_version}

    def _current_version(self, session: Session, draft: ScriptDraftModel) -> Optional[ScriptDraftVersionModel]:
        if draft.current_version_id:
            version = session.get(ScriptDraftVersionModel, draft.current_version_id)
            if version is not None:
                return version
        return (
            session.query(ScriptDraftVersionModel)
            .filter(ScriptDraftVersionModel.draft_id == draft.id)
            .order_by(ScriptDraftVersionModel.version_no.desc())
            .first()
        )

    def _draft_dict(self, row: ScriptDraftModel, current_version: Optional[ScriptDraftVersionModel]) -> Dict[str, Any]:
        return {
            "id": row.id,
            "workspaceId": row.workspace_id,
            "topicIdeaId": row.topic_idea_id,
            "title": row.title,
            "body": row.body,
            "platform": row.platform,
            "status": row.status,
            "currentVersionId": row.current_version_id,
            "adoptedVersionId": row.adopted_version_id,
            "currentVersion": self._version_dict(current_version) if current_version is not None else None,
            "updatedAt": self._dt(row.updated_at),
        }

    def _version_dict(self, row: ScriptDraftVersionModel) -> Dict[str, Any]:
        return {
            "id": row.id,
            "draftId": row.draft_id,
            "versionNo": row.version_no,
            "label": row.label,
            "platform": row.platform,
            "durationSeconds": row.duration_seconds,
            "body": row.body,
            "description": row.description,
            "tags": row.tags or [],
            "titleCandidates": row.title_candidates or [],
            "sourceType": row.source_type,
            "parentVersionId": row.parent_version_id,
            "generationId": row.generation_id,
            "status": row.status,
            "createdAt": self._dt(row.created_at),
        }

    def _draft_model(self, payload: Dict[str, Any]) -> ScriptDraftModel:
        return ScriptDraftModel(
            id=payload["id"],
            workspace_id=payload["workspaceId"],
            topic_idea_id=payload.get("topicIdeaId"),
            title=payload["title"],
            body=payload.get("body"),
            platform=payload.get("platform"),
            status=payload["status"],
            current_version_id=payload.get("currentVersionId"),
            adopted_version_id=payload.get("adoptedVersionId"),
        )

    def _version_model(self, payload: Dict[str, Any]) -> ScriptDraftVersionModel:
        return ScriptDraftVersionModel(
            id=payload["id"],
            draft_id=payload["draftId"],
            version_no=payload["versionNo"],
            label=payload["label"],
            platform=payload.get("platform"),
            duration_seconds=payload.get("durationSeconds"),
            body=payload["body"],
            description=payload.get("description"),
            tags=payload.get("tags", []),
            title_candidates=payload.get("titleCandidates", []),
            source_type=payload["sourceType"],
            parent_version_id=payload.get("parentVersionId"),
            generation_id=payload.get("generationId"),
            status=payload["status"],
        )

    def _generation_model(self, payload: Dict[str, Any]) -> AIGenerationModel:
        return AIGenerationModel(
            id=payload["id"],
            workspace_id=payload["workspaceId"],
            workflow=payload["workflow"],
            provider=payload["provider"],
            model=payload.get("model"),
            prompt_version=payload["promptVersion"],
            input_payload=payload["inputPayload"],
            evidence_ids=payload["evidenceIds"],
            output_payload=payload.get("outputPayload"),
            error=payload.get("error"),
            status=payload["status"],
        )

    def _normalize_drafts(self, generated: Dict[str, Any], request: ScriptDraftCreateRequest) -> Dict[str, Any]:
        raw_drafts = generated.get("drafts")
        drafts = raw_drafts if isinstance(raw_drafts, dict) else {}
        script = self._first_text(
            drafts,
            generated,
            keys=["script", "body", "content", "text", "scriptBody", "script_body"],
        )
        if not script:
            script = self._fallback_script(request)
        return {
            **drafts,
            "script": script,
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

    def _session(self):
        return _OptionalSession()

    def _dt(self, value: Optional[datetime]) -> Optional[str]:
        return value.isoformat() if value is not None else None

    def _now(self) -> str:
        return datetime.utcnow().isoformat()


class _OptionalSession:
    def __enter__(self) -> Optional[Session]:
        settings = get_settings()
        if not settings.postgres_host:
            return None
        engine = get_admin_engine()
        if engine is None:
            return None
        self.session = Session(engine)
        return self.session

    def __exit__(self, exc_type, exc, tb) -> None:
        session = getattr(self, "session", None)
        if session is not None:
            session.close()


script_draft_repository = ScriptDraftRepository()
