# bot.py
import asyncio
from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    Message,
)

from config import API_ID, API_HASH, BOT_TOKEN

# ───────── Engine ─────────
from engine.engine import LudoEngine
from engine.room import GameRoom
from engine.models import Player
from engine.timer import TurnTimer
from engine.ai import LudoAI

# ───────── Renderer ─────────
from renderer.board import BoardRenderer

# ───────── Database & Features ─────────
from db.database import SessionLocal
from db.wallet import deduct_coins
from features.daily import claim_daily, DailyBonusError
from features.leaderboard import get_leaderboard

# ───────────────────────────────────────
# INIT
# ───────────────────────────────────────

app = Client(
    "ludo_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)

engine = LudoEngine()
timer = TurnTimer()
ai = LudoAI()
renderer = BoardRenderer()

# ⚠️ Active rooms (later Redis)
ROOMS = {}

# ───────────────────────────────────────
# UI HELPERS
# ───────────────────────────────────────

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

# ───────────────────────────────────────
# COMMANDS
# ───────────────────────────────────────

@app.on_message(filters.command("start"))
async def start(_, msg: Message):
    await msg.reply(
        "🎲 **Welcome to Ludo Bot**\n\nChoose an option:",
        reply_markup=main_menu()
    )

# ───────────────────────────────────────
# CALLBACK HANDLER
# ───────────────────────────────────────

@app.on_callback_query()
async def callbacks(_, cq: CallbackQuery):
    data = cq.data
    user = cq.from_user

    # ───────── CREATE ROOM ─────────
    if data == "create_room":
        room = GameRoom(
            owner_id=user.id,
            entry_fee=50,
            max_players=2
        )

        room.add_player(Player(user.id, "red"))
        ROOMS[room.room_id] = room

        await cq.message.reply(
            f"🏠 **Room Created**\n"
            f"Room ID: `{room.room_id}`\n"
            f"Entry Fee: 50 coins",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "➕ Join Room",
                    callback_data=f"join:{room.room_id}"
                )]
            ])
        )

    # ───────── JOIN ROOM ─────────
    elif data.startswith("join:"):
        room_id = data.split(":")[1]
        room = ROOMS.get(room_id)

        if not room:
            await cq.answer("Room not found", show_alert=True)
            return

        db = SessionLocal()
        try:
            deduct_coins(db, user.id, room.entry_fee, "Room Entry")
        except Exception as e:
            db.close()
            await cq.answer(str(e), show_alert=True)
            return
        db.close()

        colors = ["green", "yellow", "blue"]
        color = colors[len(room.players) - 1]
        room.add_player(Player(user.id, color))

        await cq.message.reply(f"👤 **{user.first_name} joined the room**")

        if room.is_full():
            room.start_game()
            await cq.message.reply("🎮 **Game Started!**")
            await start_turn(room, cq.message)

    # ───────── DAILY BONUS ─────────
    elif data == "daily":
        db = SessionLocal()
        try:
            bonus = claim_daily(db, user.id)
            text = f"🎁 You received **{bonus} coins**!"
        except DailyBonusError as e:
            text = str(e)
        finally:
            db.close()

        await cq.answer(text, show_alert=True)

    # ───────── LEADERBOARD ─────────
    elif data == "leaderboard":
        db = SessionLocal()
        top = get_leaderboard(db)
        db.close()

        text = "🏆 **Leaderboard**\n\n"
        for p in top:
            name = p["username"] or p["user_id"]
            text += f"{p['rank']}. {name} — {p['wins']} wins\n"

        await cq.message.reply(text)

    # ───────── ROLL DICE ─────────
    elif data.startswith("roll:"):
        room_id = data.split(":")[1]
        room = ROOMS.get(room_id)
        if not room:
            return

        state = room.state
        player = state.players[state.current_turn]

        # Turn validation
        if player.user_id != user.id:
            await cq.answer("Not your turn", show_alert=True)
            return

        dice = engine.roll_dice()
        state.dice_value = dice

        await cq.message.reply(
            f"🎲 **Dice rolled:** {dice}",
            reply_markup=move_keyboard(room_id)
        )

    # ───────── MOVE TOKEN ─────────
    elif data.startswith("move:"):
        _, room_id, idx = data.split(":")
        idx = int(idx)

        room = ROOMS.get(room_id)
        if not room:
            return

        state = room.state
        player = state.players[state.current_turn]

        if player.user_id != user.id:
            await cq.answer("Not your turn", show_alert=True)
            return

        result = engine.move_token(
            player,
            idx,
            state.dice_value,
            state.players
        )

        # Render board
        image_path = renderer.render(state.players)

        await cq.message.reply_photo(
            photo=image_path,
            caption=f"♟️ Move result: **{result['result']}**"
        )

        # Turn handling
        if not result.get("bonus"):
            state.next_turn()

        await start_turn(room, cq.message)

# ───────────────────────────────────────
# TURN HANDLER
# ───────────────────────────────────────

async def start_turn(room: GameRoom, msg: Message):
    state = room.state
    player = state.players[state.current_turn]

    # AI turn
    if player.user_id < 0:
        dice = engine.roll_dice()
        idx = ai.choose_token(player, dice, state.players)
        if idx is not None:
            engine.move_token(player, idx, dice, state.players)
        state.next_turn()
        await start_turn(room, msg)
        return

    await msg.reply(
        f"🎯 **Turn:** `{player.user_id}`\nRoll the dice!",
        reply_markup=roll_keyboard(room.room_id)
    )

# ───────────────────────────────────────
# RUN
# ───────────────────────────────────────

if __name__ == "__main__":
    app.run()
        
