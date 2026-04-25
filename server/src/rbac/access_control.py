"""
Access control enforcement helpers for the smart home server.

These helpers bridge the RBAC role/permission model (see :mod:`roles`)
with the existing server protocol in ``serverService.py``.

Typical usage inside a request handler::

    from src.rbac import Permission, enforce_permission

    def handle_action(sock, unit_id, payload):
        if not enforce_permission(sock, unit_id, Permission.DEVICE_CONTROL):
            return
        # ... proceed with action
"""

from .roles import role_has_permission, normalize_role
from .role_manager import get_user_role


class AccessDeniedError(PermissionError):
    """Raised when a user does not have the required permission."""

    def __init__(self, user_id, permission, role=None):
        self.user_id = user_id
        self.permission = permission
        self.role = role
        super().__init__(
            f"User {user_id} (role={role!r}) is not allowed to perform "
            f"'{permission}'"
        )


def check_access(user_id_or_role, permission):
    """Return True if the given user or role has the permission.

    The first argument can be either a user id (looked up in the DB via
    :func:`get_user_role`) or an already-resolved role string. Strings that
    match a role name exactly are treated as roles so this works both for
    fully integrated callers and for lightweight unit tests.
    """
    if user_id_or_role is None:
        return False

    role = None
    # Try user lookup first when it looks like a user id.
    try:
        role = get_user_role(user_id_or_role)
    except Exception:
        role = None

    # Fall back to treating the argument as a role name itself.
    if role is None:
        role = normalize_role(user_id_or_role)

    return role_has_permission(role, permission)


def require_permission(user_id, permission):
    """Raise :class:`AccessDeniedError` if the user lacks the permission.

    Returns the resolved role name on success so callers can log it.
    """
    role = get_user_role(user_id)
    if not role_has_permission(role, permission):
        raise AccessDeniedError(user_id, permission, role)
    return role


def enforce_permission(sock, user_id, permission, send_error=None):
    """Enforce a permission for a socket-based request.

    Sends a protocol-level error back to the client if access is denied and
    returns ``False`` so the caller can short-circuit the handler. When the
    user is allowed the function returns ``True``.

    ``send_error`` is injected to keep this module decoupled from
    ``serverService``; if not provided we lazily import the real one.
    """
    try:
        require_permission(user_id, permission)
        return True
    except AccessDeniedError as denied:
        if send_error is None:
            try:
                from serverService import send_error as _send_error
                send_error = _send_error
            except Exception:
                send_error = None
        if send_error is not None and sock is not None:
            send_error(
                sock,
                f"Access denied: role '{denied.role}' cannot perform "
                f"'{permission}'",
            )
        return False
