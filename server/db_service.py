import json
import bcrypt
from db_init import db_execute, db_query
from datetime import datetime, timezone


def _utc_now_iso() -> str:
    """Retrun current UTC time (to keep it global) in ISO 8601 format like: 2026-02-28T16:30:00+00:00"""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def upsert_device(device_id: str, device_type: str):
    """Insert device if new; if exists, update deviceType + lastSeen."""
    time_now =  _utc_now_iso()
    db_execute("""
        INSERT INTO devices(deviceId, deviceType, lastSeen)
        VALUES(?, ?, ?)
        ON CONFLICT(deviceId) DO UPDATE SET
            deviceType = excluded.deviceType,
            lastSeen = excluded.lastSeen
    """, (device_id, device_type, time_now))


def save_ui_defination(device_id: str, ui: list):
    """Save UI definition JSON + update lastSeen."""
    time_now =  _utc_now_iso()
    # convert the Python object into a JSON string and remove extra spaces
    ui_json = json.dumps(ui, separators=(",", ":") )
    db_execute("""
        UPDATE devices
        SET uiDefinition = ?, lastSeen = ?
        WHERE deviceId = ?;            
                """, (ui_json, time_now, device_id))
  

def save_device_state(device_id: str, state: dict):
    """Save latestState JSON + update lastSeen."""
    time_now = _utc_now_iso()
    state_json = json.dumps(state, separators=(",", ":"))
    db_execute("""
        UPDATE devices
        SET latestState = ?, lastSeen = ?
        WHERE deviceId = ?;
    """, (state_json, time_now, device_id))


def fetch_devices_list():
    """Return list like: [{deviceId, deviceType}, ...]"""
    rows = db_query("SELECT deviceId, deviceType FROM devices ORDER BY deviceId;")
    # list comprehension used to double check that only device id and device type is returned.
    return [{"deviceId": r["deviceId"], "deviceType": r["deviceType"]} for r in rows]

def fetch_device_ui_and_state(device_id: str):
    """
    Return (ui_list, state_dict) if device exists in DB.
    If deviceId not found, return None.
    """
    list_rows = db_query("""
        SELECT uiDefinition, latestState
        FROM devices
        WHERE deviceId = ?;
    """, (device_id,))

    if not list_rows:
        return None  # <-- CHANGED: truly unknown device

    ui_string = list_rows[0]["uiDefinition"]
    state_string = list_rows[0]["latestState"]

    ui = json.loads(ui_string) if ui_string else []
    state = json.loads(state_string) if state_string else {}
    return ui, state


def create_user(email, password, role="unit"):
    """Creates a new user"""
   # convert password to bytes
    password_bytes = password.encode("utf-8")

    # hash the password
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())

    # store hashed password as string
    db_execute("""
        INSERT INTO users (email, password, role)
        VALUES (?, ?, ?);
    """, (email, hashed.decode("utf-8"), role))


def find_user_by_email(email):
    rows = db_query("""
        SELECT userId, email, password, role
        FROM users
        WHERE email = ?;
    """, (email,))
    return rows[0] if rows else None


def verify_login(email, password):
    """
    Returns (ok, user_dict_or_none)
    """
    user = find_user_by_email(email)
    if not user:
        return False, None

    stored_hash = user["password"].encode("utf-8")
    password_bytes = password.encode("utf-8")

    # compare password with stored hash
    if not bcrypt.checkpw(password_bytes, stored_hash):
        return False, None

    return True, {
        "userId": user["userId"],
        "email": user["email"],
        "role": user["role"] or "unit"
    }