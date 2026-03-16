from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from loguru import logger
from instagrapi import Client
from instagrapi.exceptions import ChallengeRequired
import random
import time
import json

from app.config import get_settings
from app.services.session_manager import SessionManager
from app.services.proxy_manager import ProxyManager

settings = get_settings()

DEVICE_PROFILES = [
    {
        "app_version": "269.0.0.18.75",
        "android_version": 31,
        "android_release": "11.0.0",
        "dpi": "480dpi",
        "resolution": "1080x2400",
        "manufacturer": "samsung",
        "device": "SM-A325F",
        "model": "a32",
        "cpu": "mt6768",
        "version_code": "314665256",
    },
    {
        "app_version": "269.0.0.18.75",
        "android_version": 32,
        "android_release": "12.0.0",
        "dpi": "480dpi",
        "resolution": "1080x2340",
        "manufacturer": "samsung",
        "device": "SM-A536B",
        "model": "a53x",
        "cpu": "exynos1280",
        "version_code": "314665256",
    },
    {
        "app_version": "269.0.0.18.75",
        "android_version": 33,
        "android_release": "13.0.0",
        "dpi": "440dpi",
        "resolution": "1080x2340",
        "manufacturer": "samsung",
        "device": "SM-A546B",
        "model": "a54x",
        "cpu": "exynos1380",
        "version_code": "314665256",
    },
    {
        "app_version": "269.0.0.18.75",
        "android_version": 33,
        "android_release": "13.0.0",
        "dpi": "440dpi",
        "resolution": "1080x2400",
        "manufacturer": "Xiaomi",
        "device": "Redmi Note 12",
        "model": "tapas",
        "cpu": "qcom",
        "version_code": "314665256",
    },
    {
        "app_version": "269.0.0.18.75",
        "android_version": 34,
        "android_release": "14.0.0",
        "dpi": "480dpi",
        "resolution": "1080x2340",
        "manufacturer": "Xiaomi",
        "device": "Redmi 13C",
        "model": "air",
        "cpu": "mt6769z",
        "version_code": "314665256",
    },
]


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

    def _create_client(self, username: str, proxy: Optional[str] = None, totp_seed: Optional[str] = None, device: Optional[dict] = None) -> Client:
        cl = Client()
        cl.delay_range = [1, 3]
        if device is None:
            import hashlib
            device_index = int(hashlib.md5(username.encode()).hexdigest(), 16) % len(DEVICE_PROFILES)
            device = DEVICE_PROFILES[device_index]
        cl.set_settings({
            "device_settings": {
                "app_version": device["app_version"],
                "android_version": device["android_version"],
                "android_release": device["android_release"],
                "dpi": device["dpi"],
                "resolution": device["resolution"],
                "manufacturer": device["manufacturer"],
                "device": device["device"],
                "model": device["model"],
                "cpu": device["cpu"],
                "version_code": device["version_code"],
            },
            "user_agent": (
                f"Instagram {device['app_version']} "
                f"Android ({device['android_version']}/{device['android_release']}; "
                f"{device['dpi']}; {device['resolution']}; "
                f"{device['manufacturer']}; {device['device']}; "
                f"{device['model']}; {device['cpu']}; tr_TR; {device['version_code']})"
            ),
            "country": "TR",
            "country_code": 90,
            "locale": "tr_TR",
            "timezone_offset": 10800
        })
        cl.challenge_code_handler = challenge_code_handler
        cl.change_password_handler = change_password_handler
        if proxy:
            cl.set_proxy(proxy)
        if totp_seed:
            cl.totp_seed = totp_seed
        logger.info(f"Cihaz profili secildi: {device['manufacturer']} {device['device']}")
        return cl

    def _read_device_from_session(self, username: str) -> Optional[dict]:
        """Session dosyasindan kaydedilmis cihaz bilgisini okur."""
        path = self.session_manager.session_path(username)
        if not path.exists():
            return None
        try:
            with open(path, "r") as f:
                data = json.load(f)
            ds = data.get("device_settings", {})
            if ds.get("app_version"):
                return ds
        except Exception as e:
            logger.warning(f"Session cihaz bilgisi okunamadi {username}: {e}")
        return None

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

        # Session'daki cihaz bilgisini oku - tutarlilik icin
        device = self._read_device_from_session(username)
        state.client = self._create_client(username, proxy, device=device)
        state.proxy = proxy

        if self.session_manager.load_session(state.client, username):
            if self.session_manager.verify_session(state.client):
                state.is_logged_in = True
                state.status = "active"
                logger.info(f"Hesap aktif: {username}")
            else:
                state.status = "session_expired"
                logger.warning(f"Oturum suresi dolmus veya checkpoint: {username}")

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
        state.client = self._create_client(username, proxy, totp_seed)

        if proxy:
            state.proxy = proxy
            self.proxy_manager.set_proxy(username, proxy)

        try:
            if self.session_manager.session_exists(username):
                device = self._read_device_from_session(username)
                state.client = self._create_client(username, proxy, totp_seed, device=device)
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
                except Exception as e:
                    logger.warning(f"Login exception (devam ediliyor): {e}")
            else:
                try:
                    state.client.login(username, password)
                except Exception as e:
                    logger.warning(f"Login exception (devam ediliyor): {e}")

            if not state.client.user_id:
                raise Exception("Login basarisiz - user_id bos")

            # Login sonrasi bekleme - Instagram rate limit icin
            time.sleep(3)

            self.session_manager.save_session(state.client, username)
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
        state.client = self._create_client(username, proxy, totp_seed)

        if proxy:
            state.proxy = proxy
            self.proxy_manager.set_proxy(username, proxy)

        try:
            state.client.login_by_sessionid(session_id)
            time.sleep(3)
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

    async def logout(self, username: str) -> dict:
        """[YENİ] Hesabı RAM'den çıkarır ve session dosyasını siler."""
        state = self.accounts.get(username)
        if not state:
            return {"success": False, "error": "Hesap bulunamadi"}
        try:
            self.session_manager.delete_session(username)
            del self.accounts[username]
            logger.info(f"Hesap cikis yapti: {username}")
            return {"success": True}
        except Exception as e:
            logger.error(f"Logout basarisiz {username}: {e}")
            return {"success": False, "error": str(e)}

    async def rename_account(self, old_username: str, new_username: str) -> dict:
        state = self.accounts.get(old_username)
        if not state:
            return {"success": False, "error": "Eski hesap bulunamadi"}
        try:
            old_path = self.session_manager.session_path(old_username)
            new_path = self.session_manager.session_path(new_username)
            if old_path.exists():
                old_path.rename(new_path)
            state.username = new_username
            self.accounts[new_username] = state
            del self.accounts[old_username]
            self.session_manager.save_session(state.client, new_username)
            logger.info(f"Hesap yeniden adlandirildi: {old_username} -> {new_username}")
            return {"success": True}
        except Exception as e:
            logger.error(f"Rename basarisiz {old_username}: {e}")
            return {"success": False, "error": str(e)}