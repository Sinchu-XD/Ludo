# admin/routes/stats.py
from fastapi import APIRouter, Depends
from sqlalchemy import func

from admin.auth import get_current_admin
from db.database import SessionLocal
from db.models import User, Match, Transaction

# ⚠️ TEMP: in-memory rooms (later Redis)
from bot import ROOMS

router = APIRouter()

# ───────────────────────── DASHBOARD STATS ─────────────────────────

@router.get("/")
def dashboard_stats(admin=Depends(get_current_admin)):
    """
    Main dashboard stats for admin panel
    """
    db = SessionLocal()

    total_users = db.query(func.count(User.user_id)).scalar() or 0
    banned_users = db.query(func.count(User.user_id)) \
        .filter(User.is_banned == True).scalar() or 0

    total_coins = db.query(func.sum(User.coins)).scalar() or 0

    total_matches = db.query(func.count(Match.id)).scalar() or 0

    total_transactions = db.query(func.count(Transaction.id)).scalar() or 0

    active_games = len(ROOMS)

    db.close()

    return {
        "users": {
            "total": total_users,
            "banned": banned_users,
            "active": total_users - banned_users,
        },
        "economy": {
            "total_coins": total_coins,
            "transactions": total_transactions,
        },
        "games": {
            "active_rooms": active_games,
            "matches_played": total_matches,
        },
        "status": "ok"
    }

# ───────────────────────── QUICK HEALTH CHECK ─────────────────────────

@router.get("/health")
def health_check(admin=Depends(get_current_admin)):
    """
    Simple health endpoint
    """
    return {
        "bot_running": True,
        "admin_panel": True,
        "active_rooms": len(ROOMS),
        "status": "healthy"
    }
  
