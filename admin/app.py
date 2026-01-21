# admin/app.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from admin.auth import authenticate_admin, create_access_token
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

# ───────── LOGIN ENDPOINT (VERY IMPORTANT) ─────────
@app.post("/login")
def login(data: dict):
    """
    Admin login:
    {
      "username": "admin",
      "password": "admin123"
    }
    """
    admin = authenticate_admin(
        data.get("username"),
        data.get("password")
    )

    if not admin:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({
        "username": admin["username"],
        "role": admin["role"]
    })

    return {
        "access_token": token,
        "token_type": "bearer"
    }

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
