"""Minimal authentication: register, login, me. Tokens are stored hashed."""
import re

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.user import AppUser, AuthToken
from backend.routes.forms import read_payload
from backend.schemas.auth import MeOut, TokenOut
from backend.services.ratelimit import rate_limit
from backend.services.security import hash_password, hash_token, new_token, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])
IDENTITY_KEYS = ("email", "username", "user", "login", "user_login", "user_email", "identity")
PASSWORD_KEYS = ("password", "pass", "pwd", "user_pass", "passwd")
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _first(payload: dict, keys: tuple) -> str:
    for k in keys:
        v = payload.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


def _credentials(payload: dict) -> tuple[str, str]:
    identity = _first(payload, IDENTITY_KEYS)
    password = _first(payload, PASSWORD_KEYS)
    if not identity or not password:
        raise HTTPException(status_code=422, detail="Identity and password are required.")
    return identity.lower(), password


@router.post("/register", response_model=TokenOut, dependencies=[Depends(rate_limit)])
async def register(request: Request, db: Session = Depends(get_db)):
    identity, password = _credentials(await read_payload(request))
    if "@" in identity and not _EMAIL.match(identity):
        raise HTTPException(status_code=422, detail="Invalid email address.")
    if len(password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters.")
    if db.scalar(select(AppUser).where(AppUser.identity == identity)):
        raise HTTPException(status_code=409, detail="Account already exists.")
    user = AppUser(identity=identity, password_hash=hash_password(password))
    db.add(user)
    db.flush()
    token = new_token()
    db.add(AuthToken(user_id=user.id, token_hash=hash_token(token)))
    db.commit()
    return TokenOut(token=token, message="Account created.")


@router.post("/login", response_model=TokenOut, dependencies=[Depends(rate_limit)])
async def login(request: Request, db: Session = Depends(get_db)):
    identity, password = _credentials(await read_payload(request))
    user = db.scalar(select(AppUser).where(AppUser.identity == identity))
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    token = new_token()
    db.add(AuthToken(user_id=user.id, token_hash=hash_token(token)))
    db.commit()
    return TokenOut(token=token)


def current_user(authorization: str = Header(default=""), db: Session = Depends(get_db)) -> AppUser:
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Bearer token required.")
    row = db.scalar(select(AuthToken).where(AuthToken.token_hash == hash_token(token)))
    if row is None:
        raise HTTPException(status_code=401, detail="Invalid token.")
    return db.get(AppUser, row.user_id)


@router.get("/me", response_model=MeOut)
def me(user: AppUser = Depends(current_user)):
    return MeOut(id=user.id, identity=user.identity)
