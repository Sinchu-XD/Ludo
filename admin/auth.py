# admin/auth.py
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import BaseModel

# ⚠️ Production me ENV se lo
SECRET_KEY = "SUPER_SECRET_ADMIN_KEY_CHANGE_ME"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# ───────── ADMIN CREDENTIALS (SIMPLE VERSION) ─────────
# Production me ye DB me hone chahiye
ADMIN_USERS = {
    "admin": {
        "password": "admin123",   # ⚠️ change this
        "role": "owner"
    }
}

# ───────── SCHEMAS ─────────

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

# ───────── TOKEN UTILS ─────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ───────── LOGIN ─────────

def authenticate_admin(username: str, password: str):
    admin = ADMIN_USERS.get(username)
    if not admin or admin["password"] != password:
        return None
    return {"username": username, "role": admin["role"]}

# ───────── DEPENDENCIES ─────────

def get_current_admin(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("username")
        role: str = payload.get("role")
        if username is None:
            raise credentials_exception
        return TokenData(username=username, role=role)
    except JWTError:
        raise credentials_exception

def require_owner(admin: TokenData = Depends(get_current_admin)):
    if admin.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Owner access required"
        )
    return admin
  
