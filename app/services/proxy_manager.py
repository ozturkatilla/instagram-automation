import json
from pathlib import Path
from typing import Optional, List
from loguru import logger
from app.config import get_settings

settings = get_settings()

class ProxyManager:
    def __init__(self):
        self.proxy_file = Path(settings.DATA_DIR) / "proxies.json"
        self._proxies: dict = self._load()

    def _load(self) -> dict:
        if self.proxy_file.exists():
            with open(self.proxy_file, "r") as f:
                return json.load(f)
        return {}

    def _save(self):
        self.proxy_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.proxy_file, "w") as f:
            json.dump(self._proxies, f, indent=2)

    def set_proxy(self, username: str, proxy: str):
        self._proxies[username] = proxy
        self._save()
        logger.info(f"Proxy atandı: {username} -> {proxy}")

    def get_proxy(self, username: str) -> Optional[str]:
        return self._proxies.get(username)

    def remove_proxy(self, username: str):
        if username in self._proxies:
            del self._proxies[username]
            self._save()
            logger.info(f"Proxy kaldırıldı: {username}")

    def rotate_proxy(self, username: str, proxy_pool: List[str]) -> str:
        current = self.get_proxy(username)
        if current in proxy_pool:
            idx = proxy_pool.index(current)
            next_proxy = proxy_pool[(idx + 1) % len(proxy_pool)]
        else:
            next_proxy = proxy_pool[0]
        self.set_proxy(username, next_proxy)
        return next_proxy

    def list_all(self) -> dict:
        return dict(self._proxies)