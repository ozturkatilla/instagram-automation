from pydantic import BaseModel
from typing import Optional


class LoginRequest(BaseModel):
    username: str
    password: str
    proxy: Optional[str] = None
    totp_seed: Optional[str] = None


class SessionLoginRequest(BaseModel):
    username: str
    session_id: str
    proxy: Optional[str] = None
    totp_seed: Optional[str] = None


class ChallengeSubmitRequest(BaseModel):
    username: str
    code: str
