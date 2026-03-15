import time
import asyncio
from loguru import logger


def task_send_direct(username: str, user_ids: list, message: str, delay: float = 3.0):
    """
    [BUG FIX #2] Önceki implementasyon AccountManager()'ı sıfırdan oluşturup
    session yüklemeden get_client() çağırıyordu — her zaman None dönüyordu.
    Şimdi load_all_sessions() ile disk'ten session'lar yükleniyor.
    """
    from app.services.account_manager import AccountManager
    manager = AccountManager()
    # RQ worker ayrı process'te çalışır; asyncio.run ile session'ları yükle
    asyncio.run(manager.load_all_sessions())

    client = manager.get_client(username)
    if not client:
        logger.error(f"Client bulunamadi: {username}")
        return {"error": "Client bulunamadi"}

    results = []
    for uid in user_ids:
        try:
            thread = client.direct_send(message, [uid])
            results.append({"user_id": uid, "thread_id": thread.id, "status": "sent"})
            logger.info(f"DM gönderildi: {username} -> {uid}")
        except Exception as e:
            results.append({"user_id": uid, "error": str(e), "status": "failed"})
            logger.error(f"DM gönderilemedi {uid}: {e}")
        time.sleep(delay)
    return {"results": results}


def task_get_likers(username: str, media_id: str):
    """Worker'da likers çekme görevi — session disk'ten yüklenir."""
    from app.services.account_manager import AccountManager
    manager = AccountManager()
    asyncio.run(manager.load_all_sessions())

    client = manager.get_client(username)
    if not client:
        return {"error": "Client bulunamadi"}
    likers = client.media_likers(media_id)
    return {"count": len(likers), "users": [u.username for u in likers]}