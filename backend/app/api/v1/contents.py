from typing import Dict, List

from fastapi import APIRouter, HTTPException

from app.repositories.content_item_repository import content_item_repository
from app.repositories.memory_store import repository
from app.schemas.common import ContentAsrResponse, ContentItem

router = APIRouter(prefix="/contents", tags=["contents"])


@router.get("", response_model=List[ContentItem])
def list_contents() -> List[ContentItem]:
    contents = content_item_repository.list_contents()
    if contents:
        return contents
    return repository.contents


@router.get("/{content_id}", response_model=ContentItem)
def get_content(content_id: str) -> ContentItem:
    content = content_item_repository.get_content(content_id) or repository.get_content(content_id)
    if content is None:
        raise HTTPException(status_code=404, detail="Content not found")
    return content


@router.get("/{content_id}/metrics")
def get_content_metrics(content_id: str) -> Dict[str, float]:
    content = get_content(content_id)
    engagement = content.likes + content.comments + content.saves + content.shares
    return {
        "views": content.views,
        "engagementRate": round(engagement / max(content.views, 1), 4),
        "completionRate": content.completion_rate,
        "followersGained": content.followers_gained,
        "score": content.score,
    }


@router.get("/{content_id}/analysis")
def get_content_analysis(content_id: str) -> Dict[str, object]:
    content = get_content(content_id)
    return {
        "contentId": content.id,
        "summary": "该内容适合进入复盘池，重点检查开头钩子、搜索关键词和收藏动机。",
        "strengths": ["话题焦虑明确", "评论互动充足", "涨粉转化高于近期均值"],
        "risks": ["完播率仍有优化空间"],
    }


@router.get("/{content_id}/asr", response_model=ContentAsrResponse)
def get_content_asr(content_id: str) -> ContentAsrResponse:
    asr = content_item_repository.get_asr(content_id)
    if asr is not None:
        return ContentAsrResponse(**asr)
    content = get_content(content_id)
    if not content.has_asr:
        raise HTTPException(status_code=404, detail="ASR transcript not found")
    return ContentAsrResponse(content_id=content.id, text="这里是样例 ASR 文本。后续可接入 douyin_video_asr_results 原始集合。")
