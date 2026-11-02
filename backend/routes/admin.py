"""Admin panel: HTML shell at /admin + token-protected JSON API under /api/admin."""
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.snapshot import ApiSnapshot
from backend.models.submission import Submission
from backend.models.user import AppUser, AuthToken
from backend.routes.forms import require_admin
from backend.services.security import hash_password

ui_router = APIRouter()
router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])
UI_FILE = Path(__file__).resolve().parent.parent / "admin_ui" / "index.html"


@ui_router.get("/admin", include_in_schema=False)
def admin_page():
    return FileResponse(UI_FILE, media_type="text/html")


def _collections() -> list[str]:
    try:
        from backend.services.collections import COLLECTIONS
        return sorted(COLLECTIONS)
    except ImportError:
        return []


@router.get("/summary")
def summary(db: Session = Depends(get_db)) -> dict:
    count = lambda model: db.scalar(select(func.count()).select_from(model)) or 0  # noqa: E731
    return {
        "submissions": count(Submission), "users": count(AppUser), "snapshots": count(ApiSnapshot),
        "collections": _collections(),
    }


@router.get("/submissions")
def list_submissions(slug: str | None = None, limit: int = 100, offset: int = 0, db: Session = Depends(get_db)):
    stmt = select(Submission).order_by(Submission.id.desc()).limit(min(max(limit, 1), 500)).offset(max(offset, 0))
    if slug:
        stmt = stmt.where(Submission.form_slug == slug)
    return [{"id": r.id, "form_slug": r.form_slug, "data": r.data, "created_at": r.created_at.isoformat()} for r in db.scalars(stmt)]


@router.delete("/submissions/{item_id}", status_code=204)
def delete_submission(item_id: int, db: Session = Depends(get_db)):
    row = db.get(Submission, item_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(row)
    db.commit()


@router.get("/users")
def list_users(limit: int = 200, db: Session = Depends(get_db)):
    rows = db.scalars(select(AppUser).order_by(AppUser.id.desc()).limit(min(max(limit, 1), 500)))
    return [{"id": u.id, "identity": u.identity, "created_at": u.created_at.isoformat()} for u in rows]


@router.post("/users", status_code=201)
def create_user(payload: dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    identity = str(payload.get("identity", "")).strip().lower()
    password = str(payload.get("password", ""))
    if not identity or len(identity) > 255:
        raise HTTPException(status_code=422, detail="identity is required")
    if len(password) < 8:
        raise HTTPException(status_code=422, detail="password must be at least 8 characters")
    if db.scalar(select(AppUser).where(AppUser.identity == identity)):
        raise HTTPException(status_code=409, detail="User already exists")
    user = AppUser(identity=identity, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    return {"id": user.id, "identity": user.identity}


@router.post("/users/{user_id}/password", status_code=204)
def reset_password(user_id: int, payload: dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    user = db.get(AppUser, user_id)
    password = str(payload.get("password", ""))
    if user is None:
        raise HTTPException(status_code=404, detail="Not found")
    if len(password) < 8:
        raise HTTPException(status_code=422, detail="password must be at least 8 characters")
    user.password_hash = hash_password(password)
    for t in db.scalars(select(AuthToken).where(AuthToken.user_id == user_id)):
        db.delete(t)  # sign the user out everywhere
    db.commit()


@router.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(AppUser, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(user)
    db.commit()


@router.get("/snapshots")
def list_snapshots(db: Session = Depends(get_db)):
    return [
        {"id": s.id, "path": s.path, "query": s.query, "status": s.status, "source_url": s.source_url,
         "updated_at": s.updated_at.isoformat()}
        for s in db.scalars(select(ApiSnapshot).order_by(ApiSnapshot.path, ApiSnapshot.query))
    ]


@router.get("/snapshots/{item_id}")
def get_snapshot(item_id: int, db: Session = Depends(get_db)):
    row = db.get(ApiSnapshot, item_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Not found")
    return {"id": row.id, "path": row.path, "query": row.query, "status": row.status, "body": row.body}


@router.put("/snapshots/{item_id}")
def update_snapshot(item_id: int, payload: dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    row = db.get(ApiSnapshot, item_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Not found")
    if "body" not in payload or not isinstance(payload["body"], (dict, list)):
        raise HTTPException(status_code=422, detail="body must be a JSON object or array")
    row.body = payload["body"]
    db.commit()
    return {"id": row.id, "updated": True}


@router.delete("/snapshots/{item_id}", status_code=204)
def delete_snapshot(item_id: int, db: Session = Depends(get_db)):
    row = db.get(ApiSnapshot, item_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(row)
    db.commit()
