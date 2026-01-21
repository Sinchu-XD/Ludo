# bot.py
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import API_ID, API_HASH, BOT_TOKEN

# ───────── Engine / Game ─────────
from engine.engine import LudoEngine
from engine.room import GameRoom
from engine.models import Player
from engine.ai import LudoAI
from engine.timer import TurnTimer

# ───────── Renderer ─────────
from renderer.board import BoardRenderer

# ───────── Database ─────────
from db.database import SessionLocal
from db.models import User

# ───────── Features ─────────
from features.daily import claim_daily, DailyBonusError
from features.leaderboard import get_leaderboard

# ───────── Services ─────────
from services.room_store import ROOMS
from services.match_service import MatchService
from services.anti_cheat import AntiCheatService

# ───────── INIT ─────────
app = Client("ludo_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

engine = LudoEngine()
ai = LudoAI()
renderer = BoardRenderer()
timer = TurnTimer()
match_service = MatchService(engine)

# ───────────────── UI ─────────────────

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎲 Create Room", callback_data="create_room")],
        [InlineKeyboardButton("🎁 Daily Bonus", callback_data="daily")],
        [InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")],
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

# ───────────────── START ─────────────────

@app.on_message(filters.command("start"))
async def start(_, msg):
    db = SessionLocal()
    user = db.query(User).filter(User.user_id == msg.from_user.id).first()

    if user:
        AntiCheatService.check_auto_unban(db, user)
        if user.is_banned:
            db.close()
            await msg.reply("🚫 You are banned.")
            return
        user.username = msg.from_user.username
    else:
        user = User(user_id=msg.from_user.id, username=msg.from_user.username)
        db.add(user)

    db.commit()
    db.close()
    await msg.reply("🎲 Welcome to Ludo Bot", reply_markup=main_menu())

# ───────────────── AFK HANDLER ─────────────────

async def on_turn_timeout(room_id, user_id):
    room = ROOMS.get(room_id)
    if not room or room.finished:
        return

    db = SessionLocal()
    AntiCheatService.handle_afk(db, room_id, user_id)
    db.close()

    room.state.next_turn()
    await next_turn(room)

# ───────────────── CALLBACKS ─────────────────

@app.on_callback_query()
async def cb(_, cq):
    data = cq.data
    uid = cq.from_user.id

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
        room = ROOMS.get(data.split(":")[1])
        if not room:
            return

        color = ["green", "yellow", "blue"][len(room.players) - 1]
        room.add_player(Player(uid, color))

        if room.is_full():
            match_service.start_match(room)
            await next_turn(room)

    # DAILY
    elif data == "daily":
        db = SessionLocal()
        try:
            bonus = claim_daily(db, uid)
            await cq.answer(f"+{bonus} coins", show_alert=True)
        except DailyBonusError as e:
            await cq.answer(str(e), show_alert=True)
        db.close()

    # LEADERBOARD
    elif data == "leaderboard":
        db = SessionLocal()
        data = get_leaderboard(db)
        db.close()
        text = "🏆 Leaderboard\n\n"
        for p in data:
            text += f"{p['rank']}. {p['username']} — {p['wins']} wins\n"
        await cq.message.reply(text)

    # ROLL
    elif data.startswith("roll:"):
        room = ROOMS.get(data.split(":")[1])
        if not room:
            return

        state = room.state
        player = state.players[state.current_turn]
        if player.user_id != uid:
            return

        dice = engine.roll_dice()
        state.dice_value = dice

        await timer.reset(room.room_id, uid, on_turn_timeout)
        await cq.message.reply(f"🎲 Dice: {dice}", reply_markup=move_kb(room.room_id))

    # MOVE
    elif data.startswith("move:"):
        _, rid, idx = data.split(":")
        room = ROOMS.get(rid)
        if not room:
            return

        state = room.state
        player = state.players[state.current_turn]
        if player.user_id != uid:
            return

        res = engine.move_token(player, int(idx), state.dice_value, state.players)
        img = renderer.render(state.players)

        await cq.message.reply_photo(img, caption=f"♟ {res['result']}")

        # Dice rules
        dice_rules = engine.handle_dice_rules(state, state.dice_value)

        # Match finish
        if res["player_finished"]:
            room.end_game()
            await timer.cancel(room.room_id)
            db = SessionLocal()
            match_service.finalize_match(db, room)
            db.close()
            await cq.message.reply("🏁 Match Finished!")
            return

        if not dice_rules["extra_turn"]:
            await next_turn(room)
        else:
            await next_turn(room, same_player=True)

# ───────────────── TURN ─────────────────

async def next_turn(room, same_player=False):
    state = room.state
    if not same_player:
        state.next_turn()

    p = state.players[state.current_turn]
    await timer.start(room.room_id, p.user_id, on_turn_timeout)

    await app.send_message(
        p.user_id,
        f"🎯 Your turn!",
        reply_markup=roll_kb(room.room_id)
    )

# ───────────────── RUN ─────────────────
app.run()
