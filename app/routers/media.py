from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from app.dependencies import verify_api_key, get_account_manager
from app.services.account_manager import AccountManager

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
    paths: List[str]
    caption: Optional[str] = ""

class CommentsRequest(BaseModel):
    username: str
    media_id: str
    amount: Optional[int] = 20

class CommentRequest(BaseModel):
    username: str
    media_id: str
    text: str

class CommentDeleteRequest(BaseModel):
    username: str
    media_id: str
    comment_pk: str

class CommentLikeRequest(BaseModel):
    username: str
    comment_pk: str

class CommentReplyRequest(BaseModel):
    username: str
    media_id: str
    comment_pk: str
    text: str


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
        media = client.album_upload(req.paths, caption=req.caption)
        return {"status": "ok", "media_id": str(media.pk), "media_type": "carousel"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/comments")
async def get_comments(
    req: CommentsRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    """Bir gönderinin yorumlarını çeker."""
    client = manager.get_client(req.username)
    if not client:
        raise HTTPException(status_code=404, detail="Hesap aktif değil")
    try:
        comments = client.media_comments(req.media_id, amount=req.amount)
        return {
            "status": "ok",
            "media_id": req.media_id,
            "count": len(comments),
            "comments": [
                {
                    "pk": str(c.pk),
                    "text": c.text,
                    "user_id": str(c.user.pk),
                    "username": c.user.username,
                    "created_at": str(c.created_at_utc) if c.created_at_utc else None,
                    "like_count": c.like_count
                }
                for c in comments
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/comment")
async def post_comment(
    req: CommentRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    """Bir gönderiye yorum yapar."""
    client = manager.get_client(req.username)
    if not client:
        raise HTTPException(status_code=404, detail="Hesap aktif değil")
    try:
        comment = client.media_comment(req.media_id, req.text)
        return {
            "status": "ok",
            "comment_pk": str(comment.pk),
            "text": comment.text,
            "media_id": req.media_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/comment/delete")
async def delete_comment(
    req: CommentDeleteRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    """Belirtilen yorumu siler."""
    client = manager.get_client(req.username)
    if not client:
        raise HTTPException(status_code=404, detail="Hesap aktif değil")
    try:
        result = client.comment_delete(req.media_id, req.comment_pk)
        return {"status": "ok", "deleted": result, "comment_pk": req.comment_pk}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/comment/like")
async def like_comment(
    req: CommentLikeRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    """Belirtilen yorumu beğenir."""
    client = manager.get_client(req.username)
    if not client:
        raise HTTPException(status_code=404, detail="Hesap aktif değil")
    try:
        result = client.comment_like(req.comment_pk)
        return {"status": "ok", "liked": result, "comment_pk": req.comment_pk}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/comment/reply")
async def reply_comment(
    req: CommentReplyRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    """Bir yoruma yanıt verir."""
    client = manager.get_client(req.username)
    if not client:
        raise HTTPException(status_code=404, detail="Hesap aktif değil")
    try:
        comment = client.media_comment(
            req.media_id,
            req.text,
            replied_to_comment_id=int(req.comment_pk)
        )
        return {
            "status": "ok",
            "comment_pk": str(comment.pk),
            "text": comment.text,
            "replied_to": req.comment_pk
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
class UserMediaScrapeRequest(BaseModel):
    username: str              # Gönderen hesap (sistemizdeki aktif hesap)
    target_username: str       # Scrape edilecek hesap
    start_date: str            # Başlangıç tarihi: "DD.MM.YYYY"
    end_date: str              # Bitiş tarihi: "DD.MM.YYYY"
    amount: Optional[int] = 50 # Kaç gönderi taranacak (fazla vermek daha güvenli)


@router.post("/user/scrape")
async def scrape_user_media(
    req: UserMediaScrapeRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    """
    Belirtilen kullanıcının gönderilerini tarih aralığına göre filtreler.
    Tüm medya tipleri desteklenir: photo, video, reels, carousel.
    """
    from datetime import datetime
    import pytz

    client = manager.get_client(req.username)
    if not client:
        raise HTTPException(status_code=404, detail="Hesap aktif değil")

    try:
        # Tarihleri parse et
        try:
            start = datetime.strptime(req.start_date, "%d.%m.%Y").replace(tzinfo=pytz.utc)
            end = datetime.strptime(req.end_date, "%d.%m.%Y").replace(hour=23, minute=59, second=59, tzinfo=pytz.utc)
        except ValueError:
            raise HTTPException(status_code=400, detail="Tarih formatı hatalı. Doğru format: DD.MM.YYYY")

        if start > end:
            raise HTTPException(status_code=400, detail="Başlangıç tarihi bitiş tarihinden büyük olamaz")

        # Kullanıcı ID'sini bul
        user_id = client.user_id_from_username(req.target_username)

        # Gönderileri çek
        medias = client.user_medias(user_id, amount=req.amount)

        # Medya tipi eşleştirme
        media_type_map = {
            1: "photo",
            2: "video",
            8: "carousel"
        }

        # Tarih aralığına göre filtrele
        filtered = []
        for m in medias:
            taken_at = m.taken_at
            if taken_at.tzinfo is None:
                taken_at = taken_at.replace(tzinfo=pytz.utc)

            if start <= taken_at <= end:
                # Reels tespiti: video + is_video + product_type
                media_type = media_type_map.get(m.media_type, "unknown")
                if media_type == "video" and hasattr(m, "product_type") and m.product_type == "clips":
                    media_type = "reels"

                filtered.append({
                    "media_id": str(m.pk),
                    "media_type": media_type,
                    "caption": m.caption_text if m.caption_text else "",
                    "like_count": m.like_count,
                    "comment_count": m.comment_count,
                    "taken_at": taken_at.strftime("%d.%m.%Y %H:%M"),
                    "url": f"https://www.instagram.com/p/{m.code}/"
                })

        # Tarihe göre sırala (yeniden eskiye)
        filtered.sort(key=lambda x: x["taken_at"], reverse=True)

        return {
            "status": "ok",
            "target_username": req.target_username,
            "start_date": req.start_date,
            "end_date": req.end_date,
            "total_scanned": len(medias),
            "total_found": len(filtered),
            "media": filtered
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
class MediaInfoRequest(BaseModel):
    username: str
    media_id: str

class MediaInfoByUrlRequest(BaseModel):
    username: str
    url: str


@router.post("/info")
async def get_media_info(
    req: MediaInfoRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    """Media ID ile gönderinin tüm detaylarını döndürür."""
    client = manager.get_client(req.username)
    if not client:
        raise HTTPException(status_code=404, detail="Hesap aktif değil")
    try:
        m = client.media_info(req.media_id)

        media_type_map = {1: "photo", 2: "video", 8: "carousel"}
        media_type = media_type_map.get(m.media_type, "unknown")
        if media_type == "video" and hasattr(m, "product_type") and m.product_type == "clips":
            media_type = "reels"

        return {
            "status": "ok",
            "media_id": str(m.pk),
            "media_type": media_type,
            "caption": m.caption_text if m.caption_text else "",
            "like_count": m.like_count,
            "comment_count": m.comment_count,
            "taken_at": m.taken_at.strftime("%d.%m.%Y %H:%M") if m.taken_at else None,
            "url": f"https://www.instagram.com/p/{m.code}/",
            "owner": {
                "user_id": str(m.user.pk),
                "username": m.user.username,
                "full_name": m.user.full_name if m.user.full_name else ""
            },
            "thumbnail_url": str(m.thumbnail_url) if m.thumbnail_url else None,
            "video_url": str(m.video_url) if hasattr(m, "video_url") and m.video_url else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/info_by_url")
async def get_media_info_by_url(
    req: MediaInfoByUrlRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    """Instagram linki ile gönderinin tüm detaylarını döndürür (link → bilgi tek adımda)."""
    client = manager.get_client(req.username)
    if not client:
        raise HTTPException(status_code=404, detail="Hesap aktif değil")
    try:
        media_id = client.media_pk_from_url(req.url)
        m = client.media_info(media_id)

        media_type_map = {1: "photo", 2: "video", 8: "carousel"}
        media_type = media_type_map.get(m.media_type, "unknown")
        if media_type == "video" and hasattr(m, "product_type") and m.product_type == "clips":
            media_type = "reels"

        return {
            "status": "ok",
            "media_id": str(m.pk),
            "media_type": media_type,
            "caption": m.caption_text if m.caption_text else "",
            "like_count": m.like_count,
            "comment_count": m.comment_count,
            "taken_at": m.taken_at.strftime("%d.%m.%Y %H:%M") if m.taken_at else None,
            "url": f"https://www.instagram.com/p/{m.code}/",
            "owner": {
                "user_id": str(m.user.pk),
                "username": m.user.username,
                "full_name": m.user.full_name if m.user.full_name else ""
            },
            "thumbnail_url": str(m.thumbnail_url) if m.thumbnail_url else None,
            "video_url": str(m.video_url) if hasattr(m, "video_url") and m.video_url else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))