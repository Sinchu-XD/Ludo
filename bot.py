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
from engine.engine import LudoEngine
from engine.room import GameRoom
from engine.models import Player
from engine.timer import TurnTimer
from engine.ai import LudoAI

from db.database import SessionLocal
from db.wallet import get_balance, deduct_coins
from features.daily import claim_daily, DailyBonusError
from features.leaderboard import get_leaderboard

# ───────────────────────── INIT ─────────────────────────

app = Client(
    "ludo_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)

engine = LudoEngine()
timer = TurnTimer()
ai = LudoAI()

# In-memory active rooms (Redis later)
ROOMS = {}

# ───────────────────────── HELPERS ─────────────────────────

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎲 Create Room", callback_data="create_room")],
        [InlineKeyboardButton("🎁 Daily Bonus", callback_data="daily")],
        [InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")],
    ])

# ───────────────────────── COMMANDS ─────────────────────────

@app.on_message(filters.command("start"))
async def start(_: Client, msg: Message):
    await msg.reply(
        "🎲 **Welcome to Ludo Bot**\n\nChoose an option:",
        reply_markup=main_menu()
    )

# ───────────────────────── CALLBACKS ─────────────────────────

@app.on_callback_query()
async def callbacks(_: Client, cq: CallbackQuery):
    data = cq.data
    user = cq.from_user

    # ───────── Create Room ─────────
    if data == "create_room":
        room = GameRoom(
            owner_id=user.id,
            entry_fee=50,
            max_players=2
        )

        room.add_player(Player(user.id, "red"))
        ROOMS[room.room_id] = room

        await cq.message.reply(
            f"🏠 Room Created\n"
            f"Room ID: `{room.room_id}`\n"
            f"Entry Fee: 50 coins",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "➕ Join Room",
                        callback_data=f"join:{room.room_id}"
                    )
                ]
            ])
        )

    # ───────── Join Room ─────────
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

        color = ["green", "yellow", "blue"][len(room.players) - 1]
        room.add_player(Player(user.id, color))

        await cq.message.reply(f"👤 {user.first_name} joined the room")

        if room.is_full():
            room.start_game()
            await cq.message.reply("🎮 Game Started!")

            await start_turn(room, cq.message)

    # ───────── Daily Bonus ─────────
    elif data == "daily":
        db = SessionLocal()
        try:
            bonus = claim_daily(db, user.id)
            text = f"🎁 You received {bonus} coins!"
        except DailyBonusError as e:
            text = str(e)
        finally:
            db.close()

        await cq.answer(text, show_alert=True)

    # ───────── Leaderboard ─────────
    elif data == "leaderboard":
        db = SessionLocal()
        top = get_leaderboard(db)
        db.close()

        text = "🏆 **Leaderboard**\n\n"
        for p in top:
            name = p["username"] or p["user_id"]
            text += f"{p['rank']}. {name} — {p['wins']} wins\n"

        await cq.message.reply(text)

    # ───────── Dice Roll ─────────
    elif data.startswith("roll:"):
        room_id = data.split(":")[1]
        room = ROOMS.get(room_id)
        if not room:
            return

        state = room.state
        player = state.players[state.current_turn]

        dice = engine.roll_dice()
        state.dice_value = dice

        await cq.message.reply(
            f"🎲 Dice rolled: **{dice}**",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        f"Move Token {i+1}",
                        callback_data=f"move:{room_id}:{i}"
                    )
                    for i in range(4)
                ]
            ])
        )

    # ───────── Move Token ─────────
    elif data.startswith("move:"):
        _, room_id, idx = data.split(":")
        idx = int(idx)

        room = ROOMS.get(room_id)
        if not room:
            return

        state = room.state
        player = state.players[state.current_turn]

        result = engine.move_token(
            player,
            idx,
            state.dice_value,
            state.players
        )

        await cq.message.reply(
            f"♟️ Move result: `{result['result']}`"
        )

        # Turn handling
        if not result.get("bonus"):
            state.next_turn()

        await start_turn(room, cq.message)

# ───────────────────────── TURN HANDLER ─────────────────────────

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
        f"🎯 <b>Turn:</b> {player.user_id}\nRoll the dice!",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🎲 Roll Dice",
                    callback_data=f"roll:{room.room_id}"
                )
            ]
        ])
    )

# ───────────────────────── RUN ─────────────────────────

if __name__ == "__main__":
    app.run()
  
