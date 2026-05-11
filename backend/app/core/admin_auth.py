import hashlib
import hmac
from typing import Optional

from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.routing import NoMatchFound

from sqladmin.authentication import AuthenticationBackend


ADMIN_SESSION_KEY = "vo_mate_sqladmin_user"
ADMIN_ALLOWED_ROLES = {"owner", "admin", "viewer"}


def normalize_admin_role(role: Optional[str]) -> str:
    if not role:
        return "viewer"
    normalized = role.strip().lower()
    return normalized if normalized in ADMIN_ALLOWED_ROLES else "viewer"


def admin_role_permissions(role: Optional[str]) -> dict[str, bool]:
    normalized = normalize_admin_role(role)
    return {
        "can_create": normalized in {"owner", "admin"},
        "can_edit": normalized in {"owner", "admin"},
        "can_delete": normalized == "owner",
        "can_export": normalized in {"owner", "admin", "viewer"},
        "can_view_details": normalized in {"owner", "admin", "viewer"},
    }


class AdminAuthBackend(AuthenticationBackend):
    def __init__(
        self,
        *,
        secret_key: str,
        username: str,
        password: Optional[str] = None,
        password_sha256: Optional[str] = None,
        role: str = "viewer",
    ) -> None:
        super().__init__(secret_key=secret_key)
        self.username = username
        self.password = password
        self.password_sha256 = password_sha256.lower() if password_sha256 else None
        self.role = normalize_admin_role(role)

    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = str(form.get("username") or "")
        password = str(form.get("password") or "")
        if not self._valid_credentials(username, password):
            request.session.pop(ADMIN_SESSION_KEY, None)
            return False

        request.session[ADMIN_SESSION_KEY] = {"username": self.username, "role": self.role}
        return True

    async def logout(self, request: Request) -> bool:
        request.session.pop(ADMIN_SESSION_KEY, None)
        return True

    async def authenticate(self, request: Request) -> Response | bool:
        user = request.session.get(ADMIN_SESSION_KEY)
        if isinstance(user, dict) and user.get("username") == self.username:
            return True
        try:
            login_url = request.url_for("admin:login")
        except NoMatchFound:
            login_url = "/admin/login"
        return RedirectResponse(login_url, status_code=302)

    def _valid_credentials(self, username: str, password: str) -> bool:
        if not hmac.compare_digest(username, self.username):
            return False
        if self.password is not None:
            return hmac.compare_digest(password, self.password)
        if self.password_sha256 is not None:
            digest = hashlib.sha256(password.encode("utf-8")).hexdigest()
            return hmac.compare_digest(digest, self.password_sha256)
        return False
