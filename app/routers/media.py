import asyncio
import random
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
import pytz

from app.core.dependencies import verify_api_key, get_account_manager, get_client_or_raise
from app.services.account_manager import AccountManager
from app.models.media import (
    LikersRequest,
    LikeRequest,
    PkFromUrlRequest,
    PhotoUploadRequest,
    VideoUploadRequest,
    ReelsUploadRequest,
    StoryPhotoRequest,
    StoryVideoRequest,
    CarouselUploadRequest,
    CommentsRequest,
    CommentRequest,
    CommentDeleteRequest,
    CommentLikeRequest,
    CommentReplyRequest,
    UserMediaScrapeRequest,
    MediaInfoRequest,
    MediaInfoByUrlRequest,
)

router = APIRouter()


# [BUG FIX #4] time.sleep → asyncio.sleep (event loop'u bloklamıyor)
async def _action_delay():
    await asyncio.sleep(random.uniform(2, 5))


async def _typing_delay(text: str):
    typing_time = len(text) * random.uniform(0.05, 0.1)
    await asyncio.sleep(random.uniform(2, 5) + min(typing_time, 8))


@router.post("/likers")
async def get_media_likers(
    req: LikersRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    client = get_client_or_raise(req.username, manager)
    try:
        likers = await run_in_threadpool(client.media_likers, req.media_id)
        return {
            "status": "ok",
            "media_id": req.media_id,
            "count": len(likers),
            "users": [{"pk": u.pk, "username": u.username} for u in likers]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/like")
async def like_media(
    req: LikeRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    """[YENİ] Gönderiyi beğenir."""
    client = get_client_or_raise(req.username, manager)
    try:
        await _action_delay()
        result = await run_in_threadpool(client.media_like, req.media_id)
        return {"status": "ok", "liked": result, "media_id": req.media_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/unlike")
async def unlike_media(
    req: LikeRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    """[YENİ] Gönderi beğenisini geri alır."""
    client = get_client_or_raise(req.username, manager)
    try:
        await _action_delay()
        result = await run_in_threadpool(client.media_unlike, req.media_id)
        return {"status": "ok", "unliked": result, "media_id": req.media_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pk_from_url")
async def pk_from_url(
    req: PkFromUrlRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    client = get_client_or_raise(req.username, manager)
    try:
        pk = await run_in_threadpool(client.media_pk_from_url, req.url)
        return {"status": "ok", "url": req.url, "media_pk": str(pk)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload/photo")
async def upload_photo(
    req: PhotoUploadRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    client = get_client_or_raise(req.username, manager)
    try:
        await _action_delay()
        media = await run_in_threadpool(client.photo_upload, req.image_path, caption=req.caption)
        return {"status": "ok", "media_id": str(media.pk), "media_type": "photo"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload/video")
async def upload_video(
    req: VideoUploadRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    client = get_client_or_raise(req.username, manager)
    try:
        await _action_delay()
        media = await run_in_threadpool(client.video_upload, req.video_path, caption=req.caption)
        return {"status": "ok", "media_id": str(media.pk), "media_type": "video"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload/reels")
async def upload_reels(
    req: ReelsUploadRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    client = get_client_or_raise(req.username, manager)
    try:
        await _action_delay()
        media = await run_in_threadpool(client.clip_upload, req.video_path, caption=req.caption)
        return {"status": "ok", "media_id": str(media.pk), "media_type": "reels"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload/story/photo")
async def upload_story_photo(
    req: StoryPhotoRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    client = get_client_or_raise(req.username, manager)
    try:
        await _action_delay()
        media = await run_in_threadpool(client.photo_upload_to_story, req.image_path)
        return {"status": "ok", "media_id": str(media.pk), "media_type": "story_photo"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload/story/video")
async def upload_story_video(
    req: StoryVideoRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    client = get_client_or_raise(req.username, manager)
    try:
        await _action_delay()
        media = await run_in_threadpool(client.video_upload_to_story, req.video_path)
        return {"status": "ok", "media_id": str(media.pk), "media_type": "story_video"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload/carousel")
async def upload_carousel(
    req: CarouselUploadRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    client = get_client_or_raise(req.username, manager)
    try:
        await _action_delay()
        media = await run_in_threadpool(client.album_upload, req.paths, caption=req.caption)
        return {"status": "ok", "media_id": str(media.pk), "media_type": "carousel"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/comments")
async def get_comments(
    req: CommentsRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    client = get_client_or_raise(req.username, manager)
    try:
        comments = await run_in_threadpool(client.media_comments, req.media_id, amount=req.amount)
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/comment")
async def post_comment(
    req: CommentRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    client = get_client_or_raise(req.username, manager)
    try:
        await _typing_delay(req.text)
        comment = await run_in_threadpool(client.media_comment, req.media_id, req.text)
        return {
            "status": "ok",
            "comment_pk": str(comment.pk),
            "text": comment.text,
            "media_id": req.media_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/comment/delete")
async def delete_comment(
    req: CommentDeleteRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    client = get_client_or_raise(req.username, manager)
    try:
        await _action_delay()
        result = await run_in_threadpool(client.comment_delete, req.media_id, req.comment_pk)
        return {"status": "ok", "deleted": result, "comment_pk": req.comment_pk}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/comment/like")
async def like_comment(
    req: CommentLikeRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    client = get_client_or_raise(req.username, manager)
    try:
        await _action_delay()
        result = await run_in_threadpool(client.comment_like, req.comment_pk)
        return {"status": "ok", "liked": result, "comment_pk": req.comment_pk}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/comment/reply")
async def reply_comment(
    req: CommentReplyRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    client = get_client_or_raise(req.username, manager)
    try:
        await _typing_delay(req.text)
        comment = await run_in_threadpool(
            client.media_comment,
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/user/scrape")
async def scrape_user_media(
    req: UserMediaScrapeRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    client = get_client_or_raise(req.username, manager)
    try:
        try:
            start = datetime.strptime(req.start_date, "%d.%m.%Y").replace(tzinfo=pytz.utc)
            end = datetime.strptime(req.end_date, "%d.%m.%Y").replace(hour=23, minute=59, second=59, tzinfo=pytz.utc)
        except ValueError:
            raise HTTPException(status_code=400, detail="Tarih formatı hatalı. Doğru format: DD.MM.YYYY")

        if start > end:
            raise HTTPException(status_code=400, detail="Başlangıç tarihi bitiş tarihinden büyük olamaz")

        user_id = await run_in_threadpool(client.user_id_from_username, req.target_username)
        medias = await run_in_threadpool(client.user_medias, user_id, amount=req.amount)

        media_type_map = {1: "photo", 2: "video", 8: "carousel"}
        filtered = []
        for m in medias:
            taken_at = m.taken_at
            if taken_at.tzinfo is None:
                taken_at = taken_at.replace(tzinfo=pytz.utc)
            if start <= taken_at <= end:
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


@router.post("/info")
async def get_media_info(
    req: MediaInfoRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    client = get_client_or_raise(req.username, manager)
    try:
        m = await run_in_threadpool(client.media_info, req.media_id)
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/info_by_url")
async def get_media_info_by_url(
    req: MediaInfoByUrlRequest,
    _: str = Depends(verify_api_key),
    manager: AccountManager = Depends(get_account_manager)
):
    client = get_client_or_raise(req.username, manager)
    try:
        media_id = await run_in_threadpool(client.media_pk_from_url, req.url)
        m = await run_in_threadpool(client.media_info, media_id)
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))