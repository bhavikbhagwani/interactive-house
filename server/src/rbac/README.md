# RBAC (Role-Based Access Control) — Iteration 4

This package restricts what each authenticated user can do in the smart
home server based on their **role**.

## Roles

| Role            | Description                                                      |
| --------------- | ---------------------------------------------------------------- |
| `admin`         | Full access to every feature, including admin settings and role assignment. |
| `family_member` | Normal household user. Can use devices and scenes. Cannot touch admin-only settings. *(new in Iteration 4)* |
| `guest`         | View-only access to devices and scenes. No control at all.       |

Legacy roles `user` / `unit` from earlier iterations are automatically
mapped to `family_member` so previously seeded accounts keep working.

## Permissions

Defined as string constants on `Permission`:

- `device:view`, `device:control`
- `scene:view`, `scene:trigger`, `scene:create`, `scene:delete`
- `sensor:view`, `sensor:manage`
- `automation:view`, `automation:manage`
- `role:assign`, `user:manage`, `settings:admin`

The mapping from role to permission set is declared in `roles.py` as a
`frozenset` so it cannot be mutated at runtime.

## Enforcing access on an endpoint

Wrap each handler in `serverService.py` with `enforce_permission`:

```python
from src.rbac import Permission, enforce_permission

def handle_action(sock, unit_id, payload):
    if not require_login(sock):
        return
    if not enforce_permission(sock, unit_id, Permission.DEVICE_CONTROL):
        return
    # ... existing logic
```

`enforce_permission` sends a protocol-level `error` message back to the
client (using the existing `send_error`) and returns `False` when the role
is not allowed, so handlers can short-circuit cleanly.

## Assigning and revoking roles

```python
from src.rbac import assign_role, revoke_role, get_user_role

assign_role(user_id=7, role="family_member")
get_user_role(7)      # -> "family_member"
revoke_role(7)        # -> resets to "guest"
```

`assign_role` updates the `users.role` column in the existing SQLite
database and keeps an in-memory cache so lookups stay fast. If the DB is
not reachable (for example inside an isolated unit test) the module
transparently falls back to the in-memory map.

## Package layout

```
server/src/rbac/
├── __init__.py          # Public API re-exports
├── access_control.py    # check_access / require_permission / enforce_permission
├── role_manager.py      # assign / revoke / get_user_role (DB-backed)
├── roles.py             # Permission constants + ROLES mapping
└── README.md
```
