from fastapi import Header, HTTPException, Request
from app.config import get_settings

settings = get_settings()

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Geçersiz API anahtarı")
    return x_api_key

async def get_account_manager(request: Request):
    return request.app.state.account_manager
```

**Ctrl+S** ile kaydedin.

Şimdi `app/utils/logger.py` dosyasını oluşturalım. Terminale:
```
New-Item app\utils\logger.py