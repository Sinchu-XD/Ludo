# utils/helpers.py
from typing import Optional


# ───────────────────────── TEXT HELPERS ─────────────────────────

def format_username(user_id: int, username: Optional[str]) -> str:
    """
    Safe username display
    """
    if username:
        return f"@{username}"
    return f"User({user_id})"


def format_coins(amount: int) -> str:
    """
    Human-readable coins
    """
    if amount >= 1_000_000:
        return f"{amount / 1_000_000:.1f}M"
    if amount >= 1_000:
        return f"{amount / 1_000:.1f}K"
    return str(amount)


# ───────────────────────── GAME HELPERS ─────────────────────────

def get_player_color(index: int) -> str:
    """
    Deterministic color assignment
    """
    colors = ["red", "green", "yellow", "blue"]
    return colors[index % len(colors)]


def safe_int(value, default: int = 0) -> int:
    """
    Convert to int safely
    """
    try:
        return int(value)
    except Exception:
        return default


# ───────────────────────── SECURITY HELPERS ─────────────────────────

def mask_text(text: str, visible: int = 4) -> str:
    """
    Mask sensitive text (tokens, keys)
    """
    if not text or len(text) <= visible:
        return "*" * len(text)
    return text[:visible] + "*" * (len(text) - visible)
  
