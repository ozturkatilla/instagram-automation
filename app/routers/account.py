import asyncio
from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from instagrapi.exceptions import ChallengeRequired, LoginRequired

from app.core.dependencies import verify_api_key, get_account_manager, get_client_or_raise
from app.services.account_manager import AccountManager
from app.models.account import (
    ProxyRequest,
    ProxyRotateRequest,
    PolicyRequest,
    RenameRequest,
    LogoutRequest,
    FollowRequest,
)

router = APIRouter()


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
    """Aktif olarak giriş yapmış hesapları listeler."""
    all_accounts = manager.list_accounts()
    logged_in = [acc for acc in all_accounts if acc.get("is_logged_in") is True]
    return {"status": "ok", "count": len(logged_in), "accounts": logged_in}


@router.get("/list/logged_out")
async def list_logged_out_accounts(
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    """Giriş yapılmamış (hata alan, düşen) hesapları listeler."""
    all_accounts = manager.list_accounts()
    logged_out = [acc for acc in all_accounts if acc.get("is_logged_in") is False]
    return {"status": "ok", "count": len(logged_out), "accounts": logged_out}


@router.get("/check")
async def check_account(
    username: str,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    """Hesabın gerçekten aktif olup olmadığını, checkpoint'te olup olmadığını kontrol eder."""
    state = manager.accounts.get(username)
    if not state or not state.client:
        raise HTTPException(status_code=404, detail="Hesap bulunamadi veya aktif degil")
    try:
        await run_in_threadpool(state.client.get_timeline_feed)
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


@router.post("/logout")
async def logout(
    req: LogoutRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    """[YENİ] Hesabı RAM'den çıkarır ve session dosyasını siler."""
    result = await manager.logout(req.username)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return {"status": "ok", "username": req.username, "logged_out": True}


@router.post("/follow")
async def follow_user(
    req: FollowRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    """[YENİ] Hedef kullanıcıyı takip eder."""
    client = get_client_or_raise(req.username, manager)
    try:
        await asyncio.sleep(2)
        user_id = await run_in_threadpool(client.user_id_from_username, req.target_username)
        result = await run_in_threadpool(client.user_follow, user_id)
        return {
            "status": "ok",
            "followed": result,
            "target_username": req.target_username,
            "target_user_id": str(user_id)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/unfollow")
async def unfollow_user(
    req: FollowRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    """[YENİ] Hedef kullanıcıyı takipten çıkar."""
    client = get_client_or_raise(req.username, manager)
    try:
        await asyncio.sleep(2)
        user_id = await run_in_threadpool(client.user_id_from_username, req.target_username)
        result = await run_in_threadpool(client.user_unfollow, user_id)
        return {
            "status": "ok",
            "unfollowed": result,
            "target_username": req.target_username,
            "target_user_id": str(user_id)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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