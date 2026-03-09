from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List
from app.dependencies import verify_api_key, get_account_manager
from app.services.account_manager import AccountManager
import tempfile
import os

router = APIRouter()

class LikersRequest(BaseModel):
    username: str
    media_id: str

class PkFromUrlRequest(BaseModel):
    username: str
    url: str

class PhotoUploadRequest(BaseModel):
    username: str
    image_path: str
    caption: Optional[str] = ""

class VideoUploadRequest(BaseModel):
    username: str
    video_path: str
    caption: Optional[str] = ""

class ReelsUploadRequest(BaseModel):
    username: str
    video_path: str
    caption: Optional[str] = ""

class StoryPhotoRequest(BaseModel):
    username: str
    image_path: str

class StoryVideoRequest(BaseModel):
    username: str
    video_path: str

class CarouselUploadRequest(BaseModel):
    username: str
    paths: List[str]        # Fotoğraf veya video dosya yolları listesi
    caption: Optional[str] = ""


@router.post("/likers")
async def get_media_likers(
    req: LikersRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    """Belirtilen medyanın beğenenlerini döndürür."""
    client = manager.get_client(req.username)
    if not client:
        raise HTTPException(status_code=404, detail="Hesap aktif değil")
    try:
        likers = client.media_likers(req.media_id)
        return {
            "status": "ok",
            "media_id": req.media_id,
            "count": len(likers),
            "users": [{"pk": u.pk, "username": u.username} for u in likers]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pk_from_url")
async def pk_from_url(
    req: PkFromUrlRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    """Instagram gönderi linkinden media ID (pk) döndürür."""
    client = manager.get_client(req.username)
    if not client:
        raise HTTPException(status_code=404, detail="Hesap aktif değil")
    try:
        pk = client.media_pk_from_url(req.url)
        return {"status": "ok", "url": req.url, "media_pk": str(pk)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload/photo")
async def upload_photo(
    req: PhotoUploadRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    """Sunucudaki bir fotoğrafı Instagram'a yükler."""
    client = manager.get_client(req.username)
    if not client:
        raise HTTPException(status_code=404, detail="Hesap aktif değil")
    try:
        media = client.photo_upload(req.image_path, caption=req.caption)
        return {"status": "ok", "media_id": str(media.pk), "media_type": "photo"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload/video")
async def upload_video(
    req: VideoUploadRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    """Sunucudaki bir videoyu Instagram'a yükler."""
    client = manager.get_client(req.username)
    if not client:
        raise HTTPException(status_code=404, detail="Hesap aktif değil")
    try:
        media = client.video_upload(req.video_path, caption=req.caption)
        return {"status": "ok", "media_id": str(media.pk), "media_type": "video"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload/reels")
async def upload_reels(
    req: ReelsUploadRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    """Sunucudaki bir videoyu Reels olarak yükler."""
    client = manager.get_client(req.username)
    if not client:
        raise HTTPException(status_code=404, detail="Hesap aktif değil")
    try:
        media = client.clip_upload(req.video_path, caption=req.caption)
        return {"status": "ok", "media_id": str(media.pk), "media_type": "reels"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload/story/photo")
async def upload_story_photo(
    req: StoryPhotoRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    """Sunucudaki bir fotoğrafı story olarak yükler."""
    client = manager.get_client(req.username)
    if not client:
        raise HTTPException(status_code=404, detail="Hesap aktif değil")
    try:
        media = client.photo_upload_to_story(req.image_path)
        return {"status": "ok", "media_id": str(media.pk), "media_type": "story_photo"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload/story/video")
async def upload_story_video(
    req: StoryVideoRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    """Sunucudaki bir videoyu story olarak yükler."""
    client = manager.get_client(req.username)
    if not client:
        raise HTTPException(status_code=404, detail="Hesap aktif değil")
    try:
        media = client.video_upload_to_story(req.video_path)
        return {"status": "ok", "media_id": str(media.pk), "media_type": "story_video"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload/carousel")
async def upload_carousel(
    req: CarouselUploadRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    """Birden fazla fotoğraf/videoyu carousel (albüm) olarak yükler."""
    client = manager.get_client(req.username)
    if not client:
        raise HTTPException(status_code=404, detail="Hesap aktif değil")
    try:
        from instagrapi.types import StoryMedia
        media = client.album_upload(req.paths, caption=req.caption)
        return {"status": "ok", "media_id": str(media.pk), "media_type": "carousel"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))