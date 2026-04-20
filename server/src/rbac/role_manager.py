"""
Assign and revoke roles on existing users.

Role data lives in the ``users`` table created by :mod:`db_init`. This
module wraps the DB access so the rest of the RBAC package does not depend
on SQL details. If the DB layer is unavailable (for example in unit tests
that do not spin up the real server) the module falls back to an in-memory
cache so the API keeps working.
"""

from typing import Dict, List, Optional

from .roles import (
    ROLES,
    DEFAULT_ROLE,
    ROLE_GUEST,
    normalize_role,
)


# In-memory fallback, keyed by str(user_id). Used only when the DB module
# cannot be imported (e.g. during isolated unit tests).
_memory_roles: Dict[str, str] = {}


def _db_available():
    """Return True when the server's SQLite helpers can be imported."""
    try:
        from db_init import db_execute, db_query  # noqa: F401
        return True
    except Exception:
        return False


def _normalize_user_id(user_id):
    if user_id is None:
        return None
    return str(user_id)


def assign_role(user_id, role):
    """Assign ``role`` to ``user_id``. Unknown roles raise ``ValueError``."""
    if user_id is None:
        raise ValueError("user_id is required")

    role = normalize_role(role)
    if role not in ROLES:
        raise ValueError(f"Unknown role: {role}")

    uid = _normalize_user_id(user_id)

    if _db_available():
        from db_init import db_execute
        db_execute(
            "UPDATE users SET role = ? WHERE userId = ?;",
            (role, user_id),
        )

    _memory_roles[uid] = role
    return role


def revoke_role(user_id):
    """Revoke elevated privileges from a user by resetting them to guest.

    We never fully remove a user's role because every authenticated account
    must have *some* role for the rest of the system to reason about.
    Setting the role back to ``guest`` is the safest "no privileges" state.
    """
    if user_id is None:
        raise ValueError("user_id is required")

    uid = _normalize_user_id(user_id)

    if _db_available():
        from db_init import db_execute
        db_execute(
            "UPDATE users SET role = ? WHERE userId = ?;",
            (ROLE_GUEST, user_id),
        )

    _memory_roles[uid] = ROLE_GUEST
    return ROLE_GUEST


def get_user_role(user_id) -> Optional[str]:
    """Return the normalized role for ``user_id`` or ``None`` if unknown."""
    if user_id is None:
        return None

    uid = _normalize_user_id(user_id)

    if uid in _memory_roles:
        return _memory_roles[uid]

    if _db_available():
        try:
            from db_init import db_query
            rows = db_query(
                "SELECT role FROM users WHERE userId = ?;",
                (user_id,),
            )
            if rows:
                role = normalize_role(rows[0]["role"])
                _memory_roles[uid] = role
                return role
        except Exception:
            # DB might not be initialized yet (e.g. in a fresh test run).
            return None

    return None


def list_users_with_roles() -> List[Dict[str, str]]:
    """Return ``[{userId, email, role}]`` for all users."""
    if _db_available():
        try:
            from db_init import db_query
            rows = db_query(
                "SELECT userId, email, role FROM users ORDER BY userId;"
            )
            return [
                {
                    "userId": r["userId"],
                    "email": r["email"],
                    "role": normalize_role(r["role"]),
                }
                for r in rows
            ]
        except Exception:
            pass

    # Fallback: return whatever we know from memory.
    return [
        {"userId": uid, "email": None, "role": role}
        for uid, role in sorted(_memory_roles.items())
    ]


def reset_memory_cache():
    """Utility for tests: drop the in-memory role cache."""
    _memory_roles.clear()


def ensure_default_role(user_id):
    """Ensure the user has a role assigned; default to family_member."""
    role = get_user_role(user_id)
    if role is None:
        return assign_role(user_id, DEFAULT_ROLE)
    return role
