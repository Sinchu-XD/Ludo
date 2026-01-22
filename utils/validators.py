# utils/validators.py
from typing import Optional


class ValidationError(Exception):
    """Custom validation error"""
    pass


# ───────────────────────── USER INPUT ─────────────────────────

def validate_user_id(user_id) -> int:
    """
    Ensure valid Telegram user_id
    """
    try:
        uid = int(user_id)
    except Exception:
        raise ValidationError("Invalid user ID")

    if uid <= 0:
        raise ValidationError("User ID must be positive")

    return uid


def validate_username(username: Optional[str]) -> Optional[str]:
    """
    Validate Telegram username
    """
    if username is None:
        return None

    if not isinstance(username, str):
        raise ValidationError("Invalid username type")

    if len(username) > 64:
        raise ValidationError("Username too long")

    return username.strip()


# ───────────────────────── GAME INPUT ─────────────────────────

def validate_room_id(room_id: str) -> str:
    """
    Validate room UUID
    """
    if not room_id or not isinstance(room_id, str):
        raise ValidationError("Invalid room ID")

    if len(room_id) < 8:
        raise ValidationError("Room ID too short")

    return room_id


def validate_token_index(index) -> int:
    """
    Validate token index (0–3)
    """
    try:
        idx = int(index)
    except Exception:
        raise ValidationError("Invalid token index")

    if idx < 0 or idx > 3:
        raise ValidationError("Token index out of range")

    return idx


# ───────────────────────── COINS / ECONOMY ─────────────────────────

def validate_amount(amount) -> int:
    """
    Validate coin amount
    """
    try:
        value = int(amount)
    except Exception:
        raise ValidationError("Invalid amount")

    if value <= 0:
        raise ValidationError("Amount must be positive")

    return value


# ───────────────────────── ADMIN INPUT ─────────────────────────

def validate_limit(limit, max_limit: int = 100) -> int:
    """
    Validate pagination / limits
    """
    try:
        l = int(limit)
    except Exception:
        raise ValidationError("Invalid limit")

    if l <= 0:
        raise ValidationError("Limit must be positive")

    if l > max_limit:
        return max_limit

    return l
  
