from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List

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