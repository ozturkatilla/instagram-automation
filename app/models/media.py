from pydantic import BaseModel
from typing import Optional, List


class LikersRequest(BaseModel):
    username: str
    media_id: str


class LikeRequest(BaseModel):
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


class UserMediaScrapeRequest(BaseModel):
    username: str
    target_username: str
    start_date: str
    end_date: str
    amount: Optional[int] = 50


class MediaInfoRequest(BaseModel):
    username: str
    media_id: str


class MediaInfoByUrlRequest(BaseModel):
    username: str
    url: str
