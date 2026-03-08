import time
from loguru import logger

def task_send_direct(username: str, user_ids: list, message: str, delay: float = 3.0):
    from app.services.account_manager import AccountManager
    manager = AccountManager()
    client = manager.get_client(username)
    if not client:
        logger.error(f"Client bulunamadı: {username}")
        return {"error": "Client bulunamadı"}
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
    from app.services.account_manager import AccountManager
    manager = AccountManager()
    client = manager.get_client(username)
    if not client:
        return {"error": "Client bulunamadı"}
    likers = client.media_likers(media_id)
    return {"count": len(likers), "users": [u.username for u in likers]}