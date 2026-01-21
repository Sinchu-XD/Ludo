# features/leaderboard.py
from sqlalchemy.orm import Session
from sqlalchemy import desc

from db.models import User


def get_leaderboard(
    db: Session,
    limit: int = 10,
    sort_by: str = "wins"
):
    """
    sort_by options:
    - wins
    - coins
    - total_games
    """
    if sort_by not in {"wins", "coins", "total_games"}:
        sort_by = "wins"

    column = getattr(User, sort_by)

    users = (
        db.query(User)
        .filter(User.is_banned == False)
        .order_by(desc(column))
        .limit(limit)
        .all()
    )

    leaderboard = []
    rank = 1
    for u in users:
        leaderboard.append({
            "rank": rank,
            "user_id": u.user_id,
            "username": u.username,
            "wins": u.wins,
            "coins": u.coins,
            "games": u.total_games,
        })
        rank += 1

    return leaderboard
  
