from dataclasses import dataclass

from fastapi import Header, HTTPException, status


@dataclass
class CurrentUser:
    id: str
    role: str

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


def current_user(x_user_id: str | None = Header(default=None),
                 x_user_role: str | None = Header(default=None)) -> CurrentUser:
    """Reads the headers the GATEWAY added after checking the JWT."""
    if not x_user_id or not x_user_role:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    return CurrentUser(id=x_user_id, role=x_user_role)


def admin_only(user: CurrentUser) -> None:
    if not user.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admins only")
