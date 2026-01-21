# admin/routes/users.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from admin.auth import get_current_admin, require_owner
from db.database import SessionLocal
from db.models import User
from db.wallet import add_coins, deduct_coins, WalletError

router = APIRouter()

# ───────────────────────── HELPERS ─────────────────────────

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ───────────────────────── ROUTES ─────────────────────────

@router.get("/search")
def search_user(
    user_id: int | None = None,
    username: str | None = None,
    admin=Depends(get_current_admin)
):
    db = SessionLocal()

    query = db.query(User)
    if user_id:
        query = query.filter(User.user_id == user_id)
    if username:
        query = query.filter(User.username.ilike(f"%{username}%"))

    users = query.limit(20).all()
    db.close()

    return [
        {
            "user_id": u.user_id,
            "username": u.username,
            "coins": u.coins,
            "wins": u.wins,
            "losses": u.losses,
            "is_banned": u.is_banned,
        }
        for u in users
    ]

# ───────── BAN USER ─────────
@router.post("/ban")
def ban_user(
    user_id: int,
    admin=Depends(require_owner)
):
    db = SessionLocal()
    user = db.query(User).filter(User.user_id == user_id).first()

    if not user:
        db.close()
        raise HTTPException(status_code=404, detail="User not found")

    user.is_banned = True
    db.commit()
    db.close()

    return {"status": "banned", "user_id": user_id}

# ───────── UNBAN USER ─────────
@router.post("/unban")
def unban_user(
    user_id: int,
    admin=Depends(require_owner)
):
    db = SessionLocal()
    user = db.query(User).filter(User.user_id == user_id).first()

    if not user:
        db.close()
        raise HTTPException(status_code=404, detail="User not found")

    user.is_banned = False
    db.commit()
    db.close()

    return {"status": "unbanned", "user_id": user_id}

# ───────── ADD COINS ─────────
@router.post("/add-coins")
def add_user_coins(
    user_id: int,
    amount: int,
    admin=Depends(require_owner)
):
    db = SessionLocal()
    try:
        add_coins(db, user_id, amount, reason="Admin add coins")
    except WalletError as e:
        db.close()
        raise HTTPException(status_code=400, detail=str(e))

    db.close()
    return {"status": "success", "user_id": user_id, "added": amount}

# ───────── REMOVE COINS ─────────
@router.post("/remove-coins")
def remove_user_coins(
    user_id: int,
    amount: int,
    admin=Depends(require_owner)
):
    db = SessionLocal()
    try:
        deduct_coins(db, user_id, amount, reason="Admin remove coins")
    except WalletError as e:
        db.close()
        raise HTTPException(status_code=400, detail=str(e))

    db.close()
    return {"status": "success", "user_id": user_id, "removed": amount}
  
