from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger
import os

from app.config import get_settings
from app.services.account_manager import AccountManager
from app.routers import auth, account, media, direct, health

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.SESSION_DIR, exist_ok=True)
    os.makedirs(settings.DATA_DIR, exist_ok=True)
    os.makedirs(settings.LOG_DIR, exist_ok=True)
    logger.info("Instagram Automation API başlatılıyor...")

    app.state.account_manager = AccountManager()
    await app.state.account_manager.load_all_sessions()
    logger.info("Oturumlar yüklendi.")
    yield

    logger.info("Uygulama kapatılıyor...")

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url="/docs",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, tags=["Auth"])
app.include_router(account.router, prefix="/account", tags=["Account"])
app.include_router(media.router, prefix="/media", tags=["Media"])
app.include_router(direct.router, prefix="/direct", tags=["Direct"])