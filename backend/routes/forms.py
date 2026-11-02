"""Form submission endpoints."""
import hmac

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.config import ADMIN_TOKEN
from backend.database import get_db
from backend.models.submission import Submission
from backend.schemas.forms import SubmissionAck, SubmissionOut
from backend.services.forms import FormNotFound, clean_submission
from backend.services.ratelimit import rate_limit

router = APIRouter(prefix="/api/forms", tags=["forms"])


async def read_payload(request: Request) -> dict:
    ctype = request.headers.get("content-type", "")
    if "application/json" in ctype:
        data = await request.json()
        if not isinstance(data, dict):
            raise HTTPException(status_code=422, detail="JSON object expected")
        return data
    form = await request.form()
    return {k: v for k, v in form.items() if isinstance(v, str)}


def require_admin(x_admin_token: str = Header(default="")) -> None:
    if not ADMIN_TOKEN or not hmac.compare_digest(x_admin_token, ADMIN_TOKEN):
        raise HTTPException(status_code=401, detail="Admin token required")


@router.post("/{slug}", response_model=SubmissionAck, dependencies=[Depends(rate_limit)])
async def submit(slug: str, request: Request, db: Session = Depends(get_db)):
    payload = await read_payload(request)
    try:
        cleaned = clean_submission(slug, payload)
    except FormNotFound:
        raise HTTPException(status_code=404, detail="Unknown form")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"errors": exc.args[0]})
    row = Submission(form_slug=slug, data=cleaned)
    db.add(row)
    db.commit()
    return SubmissionAck(message="Thank you! Your submission was received.", id=row.id)


@router.get("", response_model=list[SubmissionOut], dependencies=[Depends(require_admin)])
def list_submissions(slug: str | None = None, limit: int = 100, db: Session = Depends(get_db)):
    stmt = select(Submission).order_by(Submission.id.desc()).limit(min(max(limit, 1), 500))
    if slug:
        stmt = stmt.where(Submission.form_slug == slug)
    return list(db.scalars(stmt))
