from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from loguru import logger
from instagrapi import Client
from instagrapi.exceptions import ChallengeRequired

from app.config import get_settings
from app.services.session_manager import SessionManager
from app.services.proxy_manager import ProxyManager

settings = get_settings()


def challenge_code_handler(username: str, choice) -> str:
    logger.warning(f"Challenge istendi: {username}, seçenek: {choice}")
    return ""


def change_password_handler(username: str) -> str:
    logger.warning(f"Şifre değişikliği istendi: {username}")
    return ""


class AccountState:
    def __init__(self, username: str):
        self.username = username
        self.client: Optional[Client] = None
        self.is_logged_in: bool = False
        self.proxy: Optional[str] = None
        self.last_login: Optional[datetime] = None
        self.daily_actions: int = 0
        self.status: str = "idle"
        self.challenge_required: bool = False


class AccountManager:
    def __init__(self):
        self.accounts: Dict[str, AccountState] = {}
        self.session_manager = SessionManager()
        self.proxy_manager = ProxyManager()
        self.data_dir = Path(settings.DATA_DIR)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _create_client(self, proxy: Optional[str] = None) -> Client:
        cl = Client()
        cl.challenge_code_handler = challenge_code_handler
        cl.change_password_handler = change_password_handler
        if proxy:
            cl.set_proxy(proxy)
        return cl

    async def load_all_sessions(self):
        session_dir = Path(settings.SESSION_DIR)
        session_dir.mkdir(parents=True, exist_ok=True)
        for session_file in session_dir.glob("*.json"):
            username = session_file.stem
            logger.info(f"Oturum yükleniyor: {username}")
            await self._restore_account(username)

    async def _restore_account(self, username: str):
        state = AccountState(username)
        proxy = self.proxy_manager.get_proxy(username)
        state.client = self._create_client(proxy)
        state.proxy = proxy

        if self.session_manager.load_session(state.client, username):
            if self.session_manager.verify_session(state.client):
                state.is_logged_in = True
                state.status = "active"
                logger.info(f"Hesap aktif: {username}")
            else:
                state.status = "session_expired"
                logger.warning(f"Oturum süresi dolmuş: {username}")

        self.accounts[username] = state

    async def login_with_password(self, username: str, password: str, proxy: Optional[str] = None) -> bool:
        state = AccountState(username)
        state.client = self._create_client(proxy)

        if proxy:
            state.proxy = proxy
            self.proxy_manager.set_proxy(username, proxy)

        try:
            if self.session_manager.session_exists(username):
                if self.session_manager.load_session(state.client, username):
                    if self.session_manager.verify_session(state.client):
                        state.is_logged_in = True
                        state.status = "active"
                        state.last_login = datetime.now()
                        self.accounts[username] = state
                        logger.info(f"Mevcut oturum kullanıldı: {username}")
                        return True

            state.client.login(username, password)
            self.session_manager.save_session(state.client, username)
            state.is_logged_in = True
            state.status = "active"
            state.last_login = datetime.now()
            self.accounts[username] = state
            logger.info(f"Yeni login başarılı: {username}")
            return True

        except ChallengeRequired:
            state.status = "challenge_required"
            state.challenge_required = True
            self.accounts[username] = state
            logger.warning(f"Challenge gerekli: {username}")
            return False

        except Exception as e:
            state.status = "error"
            self.accounts[username] = state
            logger.error(f"Login başarısız {username}: {e}")
            return False

    async def login_with_sessionid(self, username: str, session_id: str, proxy: Optional[str] = None) -> bool:
        state = AccountState(username)
        state.client = self._create_client(proxy)

        if proxy:
            state.proxy = proxy
            self.proxy_manager.set_proxy(username, proxy)

        try:
            state.client.login_by_sessionid(session_id)
            self.session_manager.save_session(state.client, username)
            state.is_logged_in = True
            state.status = "active"
            state.last_login = datetime.now()
            self.accounts[username] = state
            logger.info(f"Session ID ile login başarılı: {username}")
            return True

        except ChallengeRequired:
            state.status = "challenge_required"
            state.challenge_required = True
            self.accounts[username] = state
            logger.warning(f"Challenge gerekli: {username}")
            return False

        except Exception as e:
            state.status = "error"
            self.accounts[username] = state
            logger.error(f"Session ID login başarısız {username}: {e}")
            return False

    async def submit_challenge_code(self, username: str, code: str) -> dict:
        """Challenge kodunu API üzerinden gönderir."""
        state = self.accounts.get(username)
        if not state or not state.client:
            return {"success": False, "error": "Hesap bulunamadı veya client yok"}
        if not state.challenge_required:
            return {"success": False, "error": "Bu hesapta aktif challenge yok"}
        try:
            state.client.challenge_code_handler = lambda u, c: code
            state.client.challenge_resolve(state.client.last_json)
            self.session_manager.save_session(state.client, username)
            state.is_logged_in = True
            state.status = "active"
            state.challenge_required = False
            logger.info(f"Challenge çözüldü: {username}")
            return {"success": True}
        except Exception as e:
            logger.error(f"Challenge çözümü başarısız {username}: {e}")
            return {"success": False, "error": str(e)}

    def get_client(self, username: str) -> Optional[Client]:
        state = self.accounts.get(username)
        if state and state.is_logged_in:
            return state.client
        return None

    def get_status(self, username: str) -> dict:
        state = self.accounts.get(username)
        if not state:
            return {"error": "Hesap bulunamadı"}
        return {
            "username": state.username,
            "is_logged_in": state.is_logged_in,
            "status": state.status,
            "proxy": state.proxy,
            "last_login": str(state.last_login) if state.last_login else None,
            "daily_actions": state.daily_actions,
            "challenge_required": state.challenge_required,
        }

    def list_accounts(self) -> list:
        return [self.get_status(u) for u in self.accounts]