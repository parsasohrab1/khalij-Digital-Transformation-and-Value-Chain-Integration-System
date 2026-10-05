"""Role-based access control (RBAC) per NFR-SEC-02."""
from __future__ import annotations

from fastapi import Depends, HTTPException, status

ROLE_HIERARCHY = {
    "operator": 1,
    "sales": 2,
    "logistics": 2,
    "analyst": 3,
    "supervisor": 4,
    "executive": 5,
    "admin": 6,
}


def role_at_least(user_role: str, required: str) -> bool:
    return ROLE_HIERARCHY.get(user_role, 0) >= ROLE_HIERARCHY.get(required, 99)


def require_roles(*allowed: str):
    """Dependency factory — must be combined with get_current_user from the api-gateway."""

    async def _check(user: dict = Depends(lambda: {})) -> dict:
        # placeholder; services override by importing auth.get_current_user
        if user.get("role") not in allowed and not role_at_least(user.get("role", ""), "admin"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access is not permitted.")
        return user

    return _check
