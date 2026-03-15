from fastapi import Header, HTTPException, Request
from app.core.config import get_settings
from typing import Optional

settings = get_settings()


async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Geçersiz API anahtarı")
    return x_api_key


async def get_account_manager(request: Request):
    return request.app.state.account_manager


def get_client_or_raise(username: str, manager):
    """
    Hesabın aktif client'ını döndürür.
    - 404: Hesap bulunamadı veya oturum açık değil
    - 429: Günlük işlem limiti aşıldı
    """
    from app.services.account_manager import DailyLimitExceeded
    try:
        client = manager.get_client(username)
    except DailyLimitExceeded as e:
        raise HTTPException(status_code=429, detail=str(e))
    if not client:
        raise HTTPException(status_code=404, detail="Hesap aktif değil")
    return client
