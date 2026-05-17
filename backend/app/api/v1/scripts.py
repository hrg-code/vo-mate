from typing import List

from fastapi import APIRouter, HTTPException

from app.repositories.script_draft_repository import script_draft_repository
from app.schemas.common import (
    ScriptCurrentVersionUpdateRequest,
    ScriptDraftCreateRequest,
    ScriptDraftDetail,
    ScriptDraftSummary,
    ScriptDraftVersionCreateRequest,
    ScriptVersionStatusUpdateRequest,
)
from app.services.script_draft_service import script_draft_service

router = APIRouter(prefix="/scripts", tags=["scripts"])


@router.get("", response_model=List[ScriptDraftSummary])
def list_script_drafts() -> List[ScriptDraftSummary]:
    return [ScriptDraftSummary(**item) for item in script_draft_repository.list_drafts()]


@router.get("/{draft_id}", response_model=ScriptDraftDetail)
def get_script_draft(draft_id: str) -> ScriptDraftDetail:
    draft = script_draft_repository.get_draft(draft_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="Script draft not found")
    return ScriptDraftDetail(**draft)

# 生成话题脚本草稿
@router.post("", response_model=ScriptDraftDetail)
def create_script_draft(payload: ScriptDraftCreateRequest) -> ScriptDraftDetail:
    return ScriptDraftDetail(**script_draft_service.create_ai_initial_draft(payload))


@router.post("/{draft_id}/versions", response_model=ScriptDraftDetail)
def create_script_draft_version(draft_id: str, payload: ScriptDraftVersionCreateRequest) -> ScriptDraftDetail:
    draft = script_draft_repository.create_version(draft_id, payload)
    if draft is None:
        raise HTTPException(status_code=404, detail="Script draft not found")
    return ScriptDraftDetail(**draft)


@router.patch("/{draft_id}/versions/{version_id}/status", response_model=ScriptDraftDetail)
def update_script_version_status(
    draft_id: str,
    version_id: str,
    payload: ScriptVersionStatusUpdateRequest,
) -> ScriptDraftDetail:
    draft = script_draft_repository.update_version_status(draft_id, version_id, payload.status)
    if draft is None:
        raise HTTPException(status_code=404, detail="Script draft version not found")
    return ScriptDraftDetail(**draft)


@router.patch("/{draft_id}/current-version", response_model=ScriptDraftDetail)
def update_script_current_version(draft_id: str, payload: ScriptCurrentVersionUpdateRequest) -> ScriptDraftDetail:
    draft = script_draft_repository.update_current_version(draft_id, payload)
    if draft is None:
        raise HTTPException(status_code=404, detail="Script draft version not found")
    return ScriptDraftDetail(**draft)
