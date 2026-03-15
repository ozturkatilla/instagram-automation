# Geriye dönük uyumluluk için app.core.dependencies'i yeniden dışa aktarır.
from app.core.dependencies import verify_api_key, get_account_manager, get_client_or_raise

__all__ = ["verify_api_key", "get_account_manager", "get_client_or_raise"]