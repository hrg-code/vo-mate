from typing import Dict

from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login() -> Dict[str, str]:
    return {"accessToken": "dev-token", "tokenType": "bearer"}


@router.post("/logout")
def logout() -> Dict[str, bool]:
    return {"ok": True}


@router.get("/me")
def me() -> Dict[str, str]:
    return {"id": "user_dev", "name": "开发用户", "role": "owner"}
