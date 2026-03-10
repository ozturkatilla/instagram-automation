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
    totp_seed: Optional[str] = None

class SessionLoginRequest(BaseModel):
    username: str
    session_id: str
    proxy: Optional[str] = None
    totp_seed: Optional[str] = None

class ChallengeSubmitRequest(BaseModel):
    username: str
    code: str


@router.post("/login")
async def login(
    req: LoginRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    """Kullanıcı adı ve şifre ile Instagram'a giriş yapar. TOTP seed varsa 2FA otomatik çözülür."""
    success = await manager.login_with_password(
        req.username, req.password, req.proxy, req.totp_seed
    )
    if not success:
        state = manager.accounts.get(req.username)
        if state and state.challenge_required:
            raise HTTPException(
                status_code=400,
                detail="challenge_required — /challenge/submit ile kodu gönderin"
            )
        raise HTTPException(status_code=400, detail="Login başarısız")
    return {"status": "ok", "username": req.username, "logged_in": True}


@router.post("/session/login_by_sessionid")
async def login_by_sessionid(
    req: SessionLoginRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    """Mevcut bir Instagram session_id ile giriş yapar."""
    success = await manager.login_with_sessionid(
        req.username, req.session_id, req.proxy, req.totp_seed
    )
    if not success:
        state = manager.accounts.get(req.username)
        if state and state.challenge_required:
            raise HTTPException(
                status_code=400,
                detail="challenge_required — /challenge/submit ile kodu gönderin"
            )
        raise HTTPException(status_code=400, detail="Session ID login başarısız")
    return {"status": "ok", "username": req.username, "logged_in": True}


@router.post("/challenge/submit")
async def challenge_submit(
    req: ChallengeSubmitRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    """Instagram challenge doğrulama kodunu gönderir."""
    result = await manager.submit_challenge_code(req.username, req.code)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Challenge çözümü başarısız"))
    return {"status": "ok", "username": req.username, "logged_in": True}