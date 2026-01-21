# admin/routes/games.py
from fastapi import APIRouter, Depends, HTTPException

from admin.auth import get_current_admin, require_owner
from db.database import SessionLocal
from db.wallet import add_coins
from db.models import Match

# ✅ SAFE shared room store (bot + admin)
from services.room_store import ROOMS

router = APIRouter()

# ───────────────────────── ACTIVE ROOMS ─────────────────────────

@router.get("/active")
def list_active_games(admin=Depends(get_current_admin)):
    """
    Returns all currently active game rooms
    """
    rooms_data = []

    for room_id, room in ROOMS.items():
        rooms_data.append({
            "room_id": room_id,
            "owner_id": room.owner_id,
            "players": [p.user_id for p in room.players],
            "started": room.started,
            "finished": room.finished,
            "entry_fee": room.entry_fee,
            "max_players": room.max_players,
        })

    return rooms_data

# ───────────────────────── FORCE END GAME ─────────────────────────

@router.post("/force-end")
def force_end_game(
    room_id: str,
    refund: bool = False,
    admin=Depends(require_owner)
):
    """
    Force stop a running game.
    Optionally refund entry fee to all players.
    """
    room = ROOMS.get(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    if refund:
        db = SessionLocal()
        for p in room.players:
            add_coins(
                db,
                user_id=p.user_id,
                amount=room.entry_fee,
                reason="Admin refund (force end)"
            )
        db.close()

    room.finished = True
    ROOMS.pop(room_id, None)

    return {
        "status": "ended",
        "room_id": room_id,
        "refunded": refund
    }

# ───────────────────────── MATCH HISTORY ─────────────────────────

@router.get("/history")
def match_history(limit: int = 20, admin=Depends(get_current_admin)):
    """
    Last completed matches
    """
    db = SessionLocal()
    matches = (
        db.query(Match)
        .order_by(Match.ended_at.desc())
        .limit(limit)
        .all()
    )
    db.close()

    return [
        {
            "id": m.id,
            "room_id": m.room_id,
            "players": m.players,
            "winners": m.winners,
            "entry_fee": m.entry_fee,
            "total_pot": m.total_pot,
            "bonus": m.bonus,
            "ended_at": m.ended_at,
        }
        for m in matches
    ]
