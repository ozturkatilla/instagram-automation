from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List

from app.dependencies import verify_api_key, get_account_manager
from app.services.account_manager import AccountManager

router = APIRouter()

class DirectMessageRequest(BaseModel):
    username: str
    user_ids: List[str]
    message: str

@router.post("/send")
async def send_direct(
    req: DirectMessageRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    client = manager.get_client(req.username)
    if not client:
        raise HTTPException(status_code=404, detail="Hesap aktif değil")
    try:
        thread = client.direct_send(req.message, req.user_ids)
        return {"status": "ok", "thread_id": thread.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))