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
    logger.warning(f"Challenge istendi: {username}, seceenek: {choice}")
    return ""


def change_password_handler(username: str) -> str:
    logger.warning(f"Sifre degisikligi istendi: {username}")
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
        self.totp_seed: Optional[str] = None


class AccountManager:
    def __init__(self):
        self.accounts: Dict[str, AccountState] = {}
        self.session_manager = SessionManager()
        self.proxy_manager = ProxyManager()
        self.data_dir = Path(settings.DATA_DIR)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _create_client(self, proxy: Optional[str] = None, totp_seed: Optional[str] = None) -> Client:
        cl = Client()
        cl.set_settings({})
        cl.set_user_agent()
        cl.challenge_code_handler = challenge_code_handler
        cl.change_password_handler = change_password_handler
        if proxy:
            cl.set_proxy(proxy)
        if totp_seed:
            cl.totp_seed = totp_seed
        return cl

    async def load_all_sessions(self):
        session_dir = Path(settings.SESSION_DIR)
        session_dir.mkdir(parents=True, exist_ok=True)
        for session_file in session_dir.glob("*.json"):
            username = session_file.stem
            logger.info(f"Oturum yukleniyor: {username}")
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
                logger.warning(f"Oturum suresi dolmus: {username}")

        self.accounts[username] = state

    async def login_with_password(
        self,
        username: str,
        password: str,
        proxy: Optional[str] = None,
        totp_seed: Optional[str] = None
    ) -> bool:
        state = AccountState(username)
        state.totp_seed = totp_seed
        state.client = self._create_client(proxy, totp_seed)

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
                        logger.info(f"Mevcut oturum kullanildi: {username}")
                        return True

            if totp_seed:
                totp_code = state.client.totp_generate_code(totp_seed)
                logger.info(f"TOTP kodu uretildi: {username}")
                try:
                    state.client.login(username, password, verification_code=totp_code)
                except Exception:
                    pass
            else:
                try:
                    state.client.login(username, password)
                except Exception:
                    pass

            self.session_manager.save_session(state.client, username)
            logger.info(f"Oturum kaydedildi (exception oncesi): {username}")
            state.is_logged_in = True
            state.status = "active"
            state.last_login = datetime.now()
            self.accounts[username] = state
            logger.info(f"Yeni login basarili: {username}")
            return True

        except ChallengeRequired:
            state.status = "challenge_required"
            state.challenge_required = True
            self.accounts[username] = state
            logger.warning(f"Challenge gerekli: {username}")
            try:
                logger.warning(f"Challenge last_json {username}: {state.client.last_json}")
            except Exception:
                pass
            return False

        except Exception as e:
            state.status = "error"
            self.accounts[username] = state
            logger.error(f"Login basarisiz {username}: {e}")
            try:
                logger.error(f"Instagram son yanit {username}: {state.client.last_json}")
            except Exception:
                pass
            return False

    async def login_with_sessionid(
        self,
        username: str,
        session_id: str,
        proxy: Optional[str] = None,
        totp_seed: Optional[str] = None
    ) -> bool:
        state = AccountState(username)
        state.totp_seed = totp_seed
        state.client = self._create_client(proxy, totp_seed)

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
            logger.info(f"Session ID ile login basarili: {username}")
            return True

        except ChallengeRequired:
            state.status = "challenge_required"
            state.challenge_required = True
            self.accounts[username] = state
            logger.warning(f"Challenge gerekli: {username}")
            try:
                logger.warning(f"Challenge last_json {username}: {state.client.last_json}")
            except Exception:
                pass
            return False

        except Exception as e:
            state.status = "error"
            self.accounts[username] = state
            logger.error(f"Session ID login basarisiz {username}: {e}")
            try:
                logger.error(f"Instagram son yanit {username}: {state.client.last_json}")
            except Exception:
                pass
            return False

    async def submit_challenge_code(self, username: str, code: str) -> dict:
        state = self.accounts.get(username)
        if not state or not state.client:
            return {"success": False, "error": "Hesap bulunamadi veya client yok"}
        if not state.challenge_required:
            return {"success": False, "error": "Bu hesapta aktif challenge yok"}
        try:
            state.client.challenge_code_handler = lambda u, c: code
            state.client.challenge_resolve(state.client.last_json)
            self.session_manager.save_session(state.client, username)
            state.is_logged_in = True
            state.status = "active"
            state.challenge_required = False
            logger.info(f"Challenge cozuldu: {username}")
            return {"success": True}
        except Exception as e:
            logger.error(f"Challenge cozumu basarisiz {username}: {e}")
            return {"success": False, "error": str(e)}

    def get_client(self, username: str) -> Optional[Client]:
        state = self.accounts.get(username)
        if state and state.is_logged_in:
            return state.client
        return None

    def get_status(self, username: str) -> dict:
        state = self.accounts.get(username)
        if not state:
            return {"error": "Hesap bulunamadi"}
        return {
            "username": state.username,
            "is_logged_in": state.is_logged_in,
            "status": state.status,
            "proxy": state.proxy,
            "last_login": str(state.last_login) if state.last_login else None,
            "daily_actions": state.daily_actions,
            "challenge_required": state.challenge_required,
            "totp_enabled": state.totp_seed is not None,
        }

    def list_accounts(self) -> list:
        return [self.get_status(u) for u in self.accounts]