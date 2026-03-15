from fastapi import APIRouter, Depends, HTTPException
from typing import Optional

from app.core.dependencies import verify_api_key, get_account_manager
from app.services.account_manager import AccountManager
from app.models.auth import LoginRequest, SessionLoginRequest, ChallengeSubmitRequest

router = APIRouter()


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
                detail="challenge_required - /challenge/submit ile kodu gonderin"
            )
        raise HTTPException(status_code=400, detail="Login basarisiz")
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
                detail="challenge_required - /challenge/submit ile kodu gonderin"
            )
        raise HTTPException(status_code=400, detail="Session ID login basarisiz")
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
        raise HTTPException(status_code=400, detail=result.get("error", "Challenge cozumu basarisiz"))
    return {"status": "ok", "username": req.username, "logged_in": True}