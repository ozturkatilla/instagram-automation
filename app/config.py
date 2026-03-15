# Geriye dönük uyumluluk için app.core.config'i yeniden dışa aktarır.
# Tüm modüller artık doğrudan app.core.config üzerinden import yapmalıdır.
from app.core.config import Settings, get_settings

__all__ = ["Settings", "get_settings"]