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
    ScriptDraftVersionCreateRequest,
    ScriptVersionStatus,
)


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

    def find_draft_for_topic(self, workspace_id: str, topic_idea_id: Optional[str], topic: str) -> Optional[Dict[str, Any]]:
        normalized_topic = topic.strip().lower()
        with self._session() as session:
            if session is not None:
                try:
                    query = session.query(ScriptDraftModel).filter(ScriptDraftModel.workspace_id == workspace_id)
                    if topic_idea_id:
                        row = query.filter(ScriptDraftModel.topic_idea_id == topic_idea_id).order_by(ScriptDraftModel.updated_at.desc()).first()
                    else:
                        row = query.filter(ScriptDraftModel.topic_idea_id.is_(None), ScriptDraftModel.topic.ilike(normalized_topic)).order_by(ScriptDraftModel.updated_at.desc()).first()
                    if row is None:
                        return None
                    return self.get_draft(row.id)
                except SQLAlchemyError:
                    session.rollback()

        for draft in self.memory_drafts.values():
            if draft.get("workspaceId") != workspace_id:
                continue
            if topic_idea_id and draft.get("topicIdeaId") == topic_idea_id:
                return self.get_draft(draft["id"])
            if not topic_idea_id and not draft.get("topicIdeaId") and str(draft.get("topic") or "").strip().lower() == normalized_topic:
                return self.get_draft(draft["id"])
        return None

    def create_draft_with_initial_version(
        self,
        draft: Dict[str, Any],
        version: Dict[str, Any],
        generation_id: str,
        generated: Dict[str, Any],
    ) -> Dict[str, Any]:
        self._persist_created(draft, version, generation_id, generated)
        return self.get_draft(draft["id"]) or {**draft, "currentVersion": version, "versions": [version]}

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
            "blocks": [block.model_dump(by_alias=True, mode="json") for block in request.blocks],
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

    def record_generation_started(
        self,
        generation_id: str,
        workspace_id: str,
        provider: str,
        model: Optional[str],
        prompt_version: str,
        input_payload: Dict[str, Any],
    ) -> None:
        record = {
            "id": generation_id,
            "workspaceId": workspace_id,
            "workflow": "script",
            "provider": provider,
            "model": model,
            "promptVersion": prompt_version,
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

    def record_generation_succeeded(self, generation_id: str, output_payload: Dict[str, Any]) -> None:
        self._finish_generation(generation_id, "succeeded", output_payload, None)

    def record_generation_failed(self, generation_id: str, error: str) -> None:
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
            "topic": row.topic,
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
            "blocks": row.blocks or [],
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
            topic=payload.get("topic"),
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
            blocks=payload.get("blocks", []),
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
