from pydantic import BaseModel
from typing import Optional, List


class ProxyRequest(BaseModel):
    username: str
    proxy: str


class ProxyRotateRequest(BaseModel):
    username: str
    proxy_pool: List[str]


class PolicyRequest(BaseModel):
    username: str
    request_delay: Optional[float] = None
    max_daily_actions: Optional[int] = None


class RenameRequest(BaseModel):
    old_username: str
    new_username: str


class LogoutRequest(BaseModel):
    username: str


class FollowRequest(BaseModel):
    username: str
    target_username: str
