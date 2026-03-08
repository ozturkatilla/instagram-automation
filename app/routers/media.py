from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.dependencies import verify_api_key, get_account_manager
from app.services.account_manager import AccountManager

router = APIRouter()

class LikersRequest(BaseModel):
    username: str
    media_id: str

@router.post("/likers")
async def get_media_likers(
    req: LikersRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    client = manager.get_client(req.username)
    if not client:
        raise HTTPException(status_code=404, detail="Hesap aktif değil")
    try:
        likers = client.media_likers(req.media_id)
        return {
            "status": "ok",
            "media_id": req.media_id,
            "count": len(likers),
            "users": [{"pk": u.pk, "username": u.username} for u in likers]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))