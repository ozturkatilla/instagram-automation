from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from instagrapi.exceptions import ChallengeRequired, LoginRequired

from app.dependencies import verify_api_key, get_account_manager
from app.services.account_manager import AccountManager

router = APIRouter()

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

@router.get("/status")
async def account_status(
    username: str,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    return manager.get_status(username)

@router.get("/list")
async def list_accounts(
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    return {"accounts": manager.list_accounts()}

@router.get("/check")
async def check_account(
    username: str,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    """Hesabin gercekten aktif olup olmadigini, checkpoint'te olup olmadigini kontrol eder."""
    state = manager.accounts.get(username)
    if not state or not state.client:
        raise HTTPException(status_code=404, detail="Hesap bulunamadi veya aktif degil")
    try:
        state.client.get_timeline_feed()
        return {"status": "ok", "username": username, "active": True, "checkpoint": False}
    except ChallengeRequired:
        state.status = "checkpoint"
        state.is_logged_in = False
        return {"status": "checkpoint", "username": username, "active": False, "checkpoint": True}
    except LoginRequired:
        state.status = "session_expired"
        state.is_logged_in = False
        return {"status": "session_expired", "username": username, "active": False, "checkpoint": False}
    except Exception as e:
        return {"status": "error", "username": username, "active": False, "error": str(e)}

@router.post("/set_proxy")
async def set_proxy(
    req: ProxyRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    manager.proxy_manager.set_proxy(req.username, req.proxy)
    state = manager.accounts.get(req.username)
    if state and state.client:
        state.client.set_proxy(req.proxy)
        state.proxy = req.proxy
    return {"status": "ok", "username": req.username, "proxy": req.proxy}

@router.post("/rotate_proxy")
async def rotate_proxy(
    req: ProxyRotateRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    new_proxy = manager.proxy_manager.rotate_proxy(req.username, req.proxy_pool)
    state = manager.accounts.get(req.username)
    if state and state.client:
        state.client.set_proxy(new_proxy)
        state.proxy = new_proxy
    return {"status": "ok", "new_proxy": new_proxy}

@router.post("/set_policy")
async def set_policy(
    req: PolicyRequest,
    _: str = Depends(verify_api_key),
):
    return {"status": "ok", "policy_updated": True}

@router.post("/rename")
async def rename_account(
    req: RenameRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    result = await manager.rename_account(req.old_username, req.new_username)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return {"status": "ok", "old_username": req.old_username, "new_username": req.new_username}

@router.get("/devices")
async def get_devices(
    username: str,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    state = manager.accounts.get(username)
    if not state or not state.client:
        raise HTTPException(status_code=404, detail="Hesap bulunamadi veya aktif degil")
    try:
        settings = state.client.get_settings()
        device_info = {
            "device": settings.get("device_settings", {}),
            "user_agent": settings.get("user_agent", ""),
            "app_version": settings.get("app_version", ""),
        }
        return {"status": "ok", "username": username, "device": device_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))