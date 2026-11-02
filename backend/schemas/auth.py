from pydantic import BaseModel


class TokenOut(BaseModel):
    token: str
    message: str = "Signed in."


class MeOut(BaseModel):
    id: int
    identity: str
