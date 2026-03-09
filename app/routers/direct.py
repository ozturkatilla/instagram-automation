from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.dependencies import verify_api_key, get_account_manager
from app.services.account_manager import AccountManager

router = APIRouter()

class DirectMessageRequest(BaseModel):
    username: str
    user_ids: List[str]
    message: str

class DirectMessageByUsernameRequest(BaseModel):
    username: str          # Gönderen hesap
    target_username: str   # Alıcının Instagram kullanıcı adı
    message: str

class DirectPhotoRequest(BaseModel):
    username: str
    user_ids: List[str]
    image_path: str

class DirectVideoRequest(BaseModel):
    username: str
    user_ids: List[str]
    video_path: str

class DirectThreadRequest(BaseModel):
    username: str
    thread_id: str
    message: str


@router.post("/send")
async def send_direct(
    req: DirectMessageRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    """Kullanıcı ID listesine DM gönderir."""
    client = manager.get_client(req.username)
    if not client:
        raise HTTPException(status_code=404, detail="Hesap aktif değil")
    try:
        thread = client.direct_send(req.message, req.user_ids)
        return {"status": "ok", "thread_id": str(thread.id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send_by_username")
async def send_direct_by_username(
    req: DirectMessageByUsernameRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    """Kullanıcı adından ID'yi bulup DM gönderir."""
    client = manager.get_client(req.username)
    if not client:
        raise HTTPException(status_code=404, detail="Hesap aktif değil")
    try:
        user_id = client.user_id_from_username(req.target_username)
        thread = client.direct_send(req.message, [str(user_id)])
        return {
            "status": "ok",
            "target_username": req.target_username,
            "target_user_id": str(user_id),
            "thread_id": str(thread.id)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send_photo")
async def send_direct_photo(
    req: DirectPhotoRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    """Kullanıcı ID listesine DM ile fotoğraf gönderir."""
    client = manager.get_client(req.username)
    if not client:
        raise HTTPException(status_code=404, detail="Hesap aktif değil")
    try:
        thread = client.direct_send_photo(req.image_path, req.user_ids)
        return {"status": "ok", "thread_id": str(thread.id), "media_type": "photo"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send_video")
async def send_direct_video(
    req: DirectVideoRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    """Kullanıcı ID listesine DM ile video gönderir."""
    client = manager.get_client(req.username)
    if not client:
        raise HTTPException(status_code=404, detail="Hesap aktif değil")
    try:
        thread = client.direct_send_video(req.video_path, req.user_ids)
        return {"status": "ok", "thread_id": str(thread.id), "media_type": "video"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reply")
async def reply_to_thread(
    req: DirectThreadRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    """Mevcut bir DM thread'ine yanıt gönderir."""
    client = manager.get_client(req.username)
    if not client:
        raise HTTPException(status_code=404, detail="Hesap aktif değil")
    try:
        thread = client.direct_send(req.message, thread_ids=[req.thread_id])
        return {"status": "ok", "thread_id": str(thread.id)}
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
    client = manager.get_client(username)
    if not client:
        raise HTTPException(status_code=404, detail="Hesap aktif değil")
    try:
        threads = client.direct_threads(amount=amount)
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
    client = manager.get_client(username)
    if not client:
        raise HTTPException(status_code=404, detail="Hesap aktif değil")
    try:
        thread = client.direct_thread(thread_id, amount=amount)
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))