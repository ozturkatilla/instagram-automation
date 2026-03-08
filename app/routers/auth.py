from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.dependencies import verify_api_key, get_account_manager
from app.services.account_manager import AccountManager

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str
    proxy: Optional[str] = None

class SessionLoginRequest(BaseModel):
    username: str
    session_id: str
    proxy: Optional[str] = None

@router.post("/login")
async def login(
    req: LoginRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    success = await manager.login_with_password(
        req.username, req.password, req.proxy
    )
    if not success:
        raise HTTPException(status_code=400, detail="Login başarısız")
    return {"status": "ok", "username": req.username, "logged_in": True}

@router.post("/session/login_by_sessionid")
async def login_by_sessionid(
    req: SessionLoginRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    success = await manager.login_with_sessionid(
        req.username, req.session_id, req.proxy
    )
    if not success:
        raise HTTPException(status_code=400, detail="Session ID login başarısız")
    return {"status": "ok", "username": req.username, "logged_in": True}