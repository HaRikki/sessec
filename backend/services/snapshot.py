"""Loads the captured API responses into the database on first start."""
import json
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.models.snapshot import ApiSnapshot

SEED_FILE = Path(__file__).resolve().parent.parent.parent / "database" / "snapshot_seed.json"


def seed_snapshots(db: Session) -> int:
    """Insert the seed file when the table is empty. Returns the number of rows inserted."""
    if not SEED_FILE.is_file() or db.scalar(select(func.count()).select_from(ApiSnapshot)):
        return 0
    rows = json.loads(SEED_FILE.read_text(encoding="utf-8"))
    for r in rows:
        db.add(ApiSnapshot(path=r["path"], query=r.get("query", ""), status=r.get("status", 200),
                           content_type=r.get("content_type", "application/json"), body=r["body"],
                           source_url=r.get("source_url")))
    db.commit()
    return len(rows)
