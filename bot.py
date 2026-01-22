# bot.py

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from contextlib import contextmanager

from config import API_ID, API_HASH, BOT_TOKEN

# ───────── Engine / Game ─────────
from engine.engine import LudoEngine
from engine.room import GameRoom, RoomError
from engine.models import Player
from engine.ai import LudoAI
from engine.timer import TurnTimer

# ───────── Renderer ─────────
from renderer.board import BoardRenderer

# ───────── Database ─────────
from db.database import SessionLocal
from db.models import User
from db.wallet import deduct_coins, add_coins, get_balance

# ───────── Features ─────────
from features.daily import claim_daily, DailyBonusError
from features.leaderboard import get_leaderboard

# ───────── Services ─────────
from services.room_store import ROOMS
from services.match_service import MatchService
from services.anti_cheat import AntiCheatService

# ───────── Utils ─────────
from utils.logger import setup_logger
from utils.validators import validate_room_id, validate_token_index, ValidationError
from utils.helpers import format_coins

# ───────── INIT ─────────

app = Client(
    "ludo_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

log = setup_logger("bot")

engine = LudoEngine()
ai = LudoAI()
renderer = BoardRenderer()
timer = TurnTimer()
match_service = MatchService(engine)

# ───────── DB HELPER ─────────

@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

# ───────── UI ─────────

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎲 Create Room", callback_data="create_room")],
        [InlineKeyboardButton("🎁 Daily Bonus", callback_data="daily")],
        [InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")]
    ])

def roll_kb(room_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎲 Roll Dice", callback_data=f"roll:{room_id}")]
    ])

def move_kb(room_id):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(f"Move {i+1}", callback_data=f"move:{room_id}:{i}")
        for i in range(4)
    ]])

# ───────── START ─────────

@app.on_message(filters.command("start") & filters.private)
async def start(_, msg):
    with get_db() as db:
        user = db.query(User).filter_by(user_id=msg.from_user.id).first()

        if user:
            AntiCheatService.check_auto_unban(db, user)
            if user.is_banned:
                await msg.reply("🚫 You are banned.")
                return
            user.username = msg.from_user.username
        else:
            db.add(User(
                user_id=msg.from_user.id,
                username=msg.from_user.username
            ))

    await msg.reply("🎲 Welcome to Ludo Bot", reply_markup=main_menu())

# ───────── AFK HANDLER ─────────

async def on_turn_timeout(room_id, user_id):
    room = ROOMS.get(room_id)
    if not room or room.finished:
        return

    log.warning(f"AFK timeout | room={room_id} user={user_id}")

    with get_db() as db:
        AntiCheatService.handle_afk(db, room_id, user_id)

    await next_turn(room)

# ───────── CALLBACKS ─────────

@app.on_callback_query(filters.private)
async def cb(_, cq):
    uid = cq.from_user.id
    data = cq.data

    # CREATE ROOM
    if data == "create_room":
        room = GameRoom(uid, entry_fee=50, max_players=2)
        room.add_player(Player(uid, "red"))
        ROOMS[room.room_id] = room

        await cq.message.reply(
            f"🏠 Room `{room.room_id}` created",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Join", callback_data=f"join:{room.room_id}")]
            ])
        )

    # JOIN ROOM
    elif data.startswith("join:"):
        _, rid = data.split(":")
        rid = validate_room_id(rid)

        room = ROOMS.get(rid)
        if not room:
            await cq.answer("Room not found", show_alert=True)
            return

        try:
            with get_db() as db:
                deduct_coins(
                    db,
                    user_id=uid,
                    amount=room.entry_fee,
                    reason="join_room"
                )

            color = ["green", "yellow", "blue"][len(room.players) - 1]
            room.add_player(Player(uid, color))

        except RoomError as e:
            await cq.answer(str(e), show_alert=True)
            return
        except Exception as e:
            await cq.answer(str(e), show_alert=True)
            return

        if room.is_full():
            match_service.start_match(room)
            await next_turn(room)

    # DAILY BONUS
    elif data == "daily":
        with get_db() as db:
            try:
                bonus = claim_daily(db, uid)
                await cq.answer(f"🎁 +{format_coins(bonus)} coins", show_alert=True)
            except DailyBonusError as e:
                await cq.answer(str(e), show_alert=True)

    # LEADERBOARD
    elif data == "leaderboard":
        with get_db() as db:
            top = get_leaderboard(db)

        text = "🏆 Leaderboard\n\n"
        for p in top:
            text += f"{p['rank']}. {p['username']} — {p['wins']} wins\n"

        await cq.message.reply(text)

    # ROLL DICE
    elif data.startswith("roll:"):
        _, rid = data.split(":")
        rid = validate_room_id(rid)

        room = ROOMS.get(rid)
        if not room:
            return

        state = room.state
        player = state.players[state.current_turn]

        if player.user_id != uid:
            return

        state.dice_value = engine.roll_dice()
        await timer.reset(room.room_id, uid, on_turn_timeout)

        await cq.message.reply(
            f"🎲 Dice: {state.dice_value}",
            reply_markup=move_kb(room.room_id)
        )

    # MOVE TOKEN
    elif data.startswith("move:"):
        _, rid, idx = data.split(":")
        rid = validate_room_id(rid)
        idx = validate_token_index(idx)

        room = ROOMS.get(rid)
        if not room:
            return

        state = room.state
        player = state.players[state.current_turn]

        if player.user_id != uid:
            return

        res = engine.move_token(
            player,
            idx,
            state.dice_value,
            state.players
        )

        await cq.message.reply_photo(
            renderer.render(state.players),
            caption=f"♟ {res['result']}"
        )

        if res["player_finished"]:
            room.end_game()
            await timer.cancel(room.room_id)

            with get_db() as db:
                match_service.finalize_match(db, room)

            await cq.message.reply("🏁 Match Finished!")
            return

        if not engine.handle_dice_rules(state, state.dice_value)["extra_turn"]:
            await next_turn(room)
        else:
            await next_turn(room, same_player=True)

# ───────── TURN ─────────

async def next_turn(room, same_player=False):
    if not same_player:
        room.state.next_turn()

    player = room.state.players[room.state.current_turn]
    await timer.start(room.room_id, player.user_id, on_turn_timeout)

    await app.send_message(
        player.user_id,
        "🎯 Your turn! Roll the dice.",
        reply_markup=roll_kb(room.room_id)
    )

# ───────── RUN ─────────

log.info("Bot starting...")
app.run()
