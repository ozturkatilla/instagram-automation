import json
from pathlib import Path
from loguru import logger
from instagrapi import Client
from app.config import get_settings

settings = get_settings()

class SessionManager:
    def __init__(self):
        self.session_dir = Path(settings.SESSION_DIR)
        self.session_dir.mkdir(parents=True, exist_ok=True)

    def session_path(self, username: str) -> Path:
        return self.session_dir / f"{username}.json"

    def session_exists(self, username: str) -> bool:
        return self.session_path(username).exists()

    def save_session(self, client: Client, username: str) -> bool:
        try:
            path = self.session_path(username)
            client.dump_settings(path)
            logger.info(f"Oturum kaydedildi: {username}")
            return True
        except Exception as e:
            logger.error(f"Oturum kaydedilemedi {username}: {e}")
            return False

    def load_session(self, client: Client, username: str) -> bool:
        path = self.session_path(username)
        if not path.exists():
            logger.warning(f"Oturum dosyasi bulunamadi: {username}")
            return False
        try:
            client.load_settings(path)
            logger.info(f"Oturum yuklendi: {username}")
            return True
        except Exception as e:
            logger.error(f"Oturum yuklenemedi {username}: {e}")
            return False

    def delete_session(self, username: str) -> bool:
        path = self.session_path(username)
        if path.exists():
            path.unlink()
            logger.info(f"Oturum silindi: {username}")
            return True
        return False

    def verify_session(self, client: Client) -> bool:
        try:
            if client.user_id:
                return True
            return False
        except Exception as e:
            logger.warning(f"Oturum dogrulama basarisiz: {e}")
            return False