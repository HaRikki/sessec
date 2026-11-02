from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SubmissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    form_slug: str
    data: dict
    created_at: datetime


class SubmissionAck(BaseModel):
    ok: bool = True
    message: str
    id: int
