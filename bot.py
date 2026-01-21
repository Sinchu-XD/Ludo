# bot.py
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import API_ID, API_HASH, BOT_TOKEN

# ───────── Engine ─────────
from engine.engine import LudoEngine
from engine.room import GameRoom
from engine.models import Player
from engine.ai import LudoAI

# ───────── Renderer ─────────
from renderer.board import BoardRenderer

# ───────── Database & Features ─────────
from db.database import SessionLocal
from db.models import User
from db.wallet import deduct_coins
from features.daily import claim_daily, DailyBonusError
from features.leaderboard import get_leaderboard

# ───────── Shared Rooms ─────────
from services.room_store import ROOMS

app = Client("ludo_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

engine = LudoEngine()
ai = LudoAI()
renderer = BoardRenderer()

# ───────── UI HELPERS ─────────
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎲 Create Room", callback_data="create_room")],
        [InlineKeyboardButton("🎁 Daily Bonus", callback_data="daily")],
        [InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")],
    ])

def roll_keyboard(room_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎲 Roll Dice", callback_data=f"roll:{room_id}")]
    ])

def move_keyboard(room_id):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(f"Move {i+1}", callback_data=f"move:{room_id}:{i}")
        for i in range(4)
    ]])

# ───────── START ─────────
@app.on_message(filters.command("start"))
async def start(_, msg):
    db = SessionLocal()
    user = db.query(User).filter(User.user_id == msg.from_user.id).first()

    if user and user.is_banned:
        db.close()
        await msg.reply("🚫 You are banned from using this bot.")
        return

    if not user:
        user = User(
            user_id=msg.from_user.id,
            username=msg.from_user.username,
            coins=0
        )
        db.add(user)
    else:
        user.username = msg.from_user.username

    db.commit()
    db.close()

    await msg.reply(
        "🎲 **Welcome to Ludo Bot**\n\nChoose an option:",
        reply_markup=main_menu()
    )

# ───────── CALLBACKS ─────────
@app.on_callback_query()
async def callbacks(_, cq):
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

        db = SessionLocal()
        deduct_coins(db, uid, room.entry_fee, "Room Entry")
        db.close()

        color = ["green", "yellow", "blue"][len(room.players) - 1]
        room.add_player(Player(uid, color))

        if room.is_full():
            room.start_game()
            await next_turn(room, cq.message)

    # DAILY BONUS
    elif data == "daily":
        db = SessionLocal()
        try:
            bonus = claim_daily(db, uid)
            await cq.answer(f"🎁 +{bonus} coins", show_alert=True)
        except DailyBonusError as e:
            await cq.answer(str(e), show_alert=True)
        db.close()

    # LEADERBOARD
    elif data == "leaderboard":
        db = SessionLocal()
        top = get_leaderboard(db)
        db.close()

        text = "🏆 Leaderboard\n\n"
        for p in top:
            name = p["username"] or p["user_id"]
            text += f"{p['rank']}. {name} — {p['wins']} wins\n"
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
        await cq.message.reply(f"🎲 Dice: {dice}", reply_markup=move_keyboard(room.room_id))

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

        if not res["bonus"]:
            state.next_turn()

        await next_turn(room, cq.message)

# ───────── TURN HANDLER ─────────
async def next_turn(room, msg):
    if room.finished:
        ROOMS.pop(room.room_id, None)
        return

    p = room.state.players[room.state.current_turn]
    await msg.reply(
        f"🎯 Turn: {p.user_id}",
        reply_markup=roll_keyboard(room.room_id)
    )

# ───────── RUN ─────────
app.run()
    
