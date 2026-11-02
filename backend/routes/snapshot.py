"""Serves the captured API responses at the same paths the original frontend calls (GET only)."""
from urllib.parse import parse_qsl, urlencode

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.snapshot import ApiSnapshot
from backend.services.snapshot_manifest import PATHS

router = APIRouter(tags=["snapshot"])


def _canonical(query: str) -> str:
    return urlencode(sorted(parse_qsl(query, keep_blank_values=True)))


def _make_handler(path: str):
    def handler(request: Request, db: Session = Depends(get_db)):
        wanted = _canonical(request.url.query)
        row = db.scalar(select(ApiSnapshot).where(ApiSnapshot.path == path, ApiSnapshot.query == wanted))
        if row is None:  # same endpoint, different query string: fall back to the first stored variant
            row = db.scalar(select(ApiSnapshot).where(ApiSnapshot.path == path).order_by(ApiSnapshot.id).limit(1))
        if row is None:
            raise HTTPException(status_code=404, detail="No stored response for this endpoint")
        return JSONResponse(row.body, status_code=row.status)

    return handler


for _path in PATHS:
    router.add_api_route(_path, _make_handler(_path), methods=["GET"], name=f"snapshot:{_path}", include_in_schema=False)
