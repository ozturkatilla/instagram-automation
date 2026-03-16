import asyncio
import random
from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool

from app.core.dependencies import verify_api_key, get_account_manager, get_client_or_raise
from app.services.account_manager import AccountManager
from app.models.direct import (
    DirectMessageRequest,
    DirectMessageByUsernameRequest,
    DirectPhotoRequest,
    DirectVideoRequest,
    DirectThreadRequest,
)

router = APIRouter()


# [BUG FIX #3] time.sleep → asyncio.sleep (event loop'u bloklamıyor)
async def _human_typing_delay(message: str):
    msg_len = len(message) if message else 0
    typing_time = msg_len * random.uniform(0.05, 0.1)
    total_delay = random.uniform(2, 5) + min(typing_time, 8)
    await asyncio.sleep(total_delay)


async def _action_delay():
    await asyncio.sleep(random.uniform(2, 5))


@router.post("/send")
async def send_direct(
    req: DirectMessageRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    """Kullanıcı ID listesine DM gönderir."""
    client = get_client_or_raise(req.username, manager)
    try:
        user_ids_int = []
        for uid in req.user_ids:
            try:
                user_ids_int.append(int(uid))
            except (ValueError, TypeError):
                continue
                
        if not user_ids_int:
            raise HTTPException(status_code=400, detail="Geçerli user_id bulunamadı")
            
        await _human_typing_delay(req.message)
        # [BUG FIX #3] instagrapi senkron çağrısı thread pool'a taşındı
        thread = await run_in_threadpool(client.direct_send, req.message, user_ids_int)
        return {"status": "ok", "thread_id": str(thread.id)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send_by_username")
async def send_direct_by_username(
    req: DirectMessageByUsernameRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    """Kullanıcı adından ID'yi bulup DM gönderir."""
    client = get_client_or_raise(req.username, manager)
    try:
        user_id = await run_in_threadpool(client.user_id_from_username, req.target_username)
        await _human_typing_delay(req.message)
        thread = await run_in_threadpool(client.direct_send, req.message, [int(user_id)])
        return {
            "status": "ok",
            "target_username": req.target_username,
            "target_user_id": str(user_id),
            "thread_id": str(thread.id)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send_photo")
async def send_direct_photo(
    req: DirectPhotoRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    """Kullanıcı ID listesine DM ile fotoğraf gönderir."""
    client = get_client_or_raise(req.username, manager)
    try:
        user_ids_int = [int(uid) for uid in req.user_ids]
        await _action_delay()
        thread = await run_in_threadpool(client.direct_send_photo, req.image_path, user_ids_int)
        return {"status": "ok", "thread_id": str(thread.id), "media_type": "photo"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send_video")
async def send_direct_video(
    req: DirectVideoRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    """Kullanıcı ID listesine DM ile video gönderir."""
    client = get_client_or_raise(req.username, manager)
    try:
        user_ids_int = [int(uid) for uid in req.user_ids]
        await _action_delay()
        thread = await run_in_threadpool(client.direct_send_video, req.video_path, user_ids_int)
        return {"status": "ok", "thread_id": str(thread.id), "media_type": "video"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reply")
async def reply_to_thread(
    req: DirectThreadRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    """Mevcut bir DM thread'ine yanıt gönderir."""
    client = get_client_or_raise(req.username, manager)
    try:
        await _human_typing_delay(req.message)
        thread = await run_in_threadpool(
            client.direct_send, req.message, [], [int(req.thread_id)]
        )
        return {"status": "ok", "thread_id": str(thread.id)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/threads")
async def get_threads(
    username: str,
    amount: int = 20,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    """Hesabın DM thread listesini döndürür."""
    client = get_client_or_raise(username, manager)
    try:
        threads = await run_in_threadpool(client.direct_threads, amount=amount)
        return {
            "status": "ok",
            "count": len(threads),
            "threads": [
                {
                    "thread_id": str(t.id),
                    "users": [{"pk": str(u.pk), "username": u.username} for u in t.users],
                    "last_activity": str(t.last_activity_at) if t.last_activity_at else None
                }
                for t in threads
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/thread/messages")
async def get_thread_messages(
    username: str,
    thread_id: str,
    amount: int = 20,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    """Belirli bir thread'deki mesajları döndürür."""
    client = get_client_or_raise(username, manager)
    try:
        thread = await run_in_threadpool(client.direct_thread, int(thread_id), amount=amount)
        return {
            "status": "ok",
            "thread_id": thread_id,
            "messages": [
                {
                    "item_id": str(m.id),
                    "user_id": str(m.user_id),
                    "text": m.text if m.text else None,
                    "timestamp": str(m.timestamp) if m.timestamp else None,
                    "item_type": m.item_type
                }
                for m in thread.messages
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))