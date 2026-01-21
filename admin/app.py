# admin/app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from admin.routes import users, games, stats

app = FastAPI(
    title="Ludo Bot Admin Panel",
    description="Admin control panel for Telegram Ludo Bot",
    version="1.0.0"
)

# ───────── CORS (frontend ke liye) ─────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # production me domain set karna
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ───────── ROUTES ─────────
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(games.router, prefix="/games", tags=["Games"])
app.include_router(stats.router, prefix="/stats", tags=["Stats"])

# ───────── ROOT ─────────
@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "Ludo Admin Panel",
        "version": "1.0.0"
    }
  
