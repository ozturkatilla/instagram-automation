from pydantic import BaseModel
from typing import List, Optional


class DirectMessageRequest(BaseModel):
    username: str
    user_ids: List[str]
    message: str


class DirectMessageByUsernameRequest(BaseModel):
    username: str
    target_username: str
    message: str


class DirectPhotoRequest(BaseModel):
    username: str
    user_ids: List[str]
    image_path: str


class DirectVideoRequest(BaseModel):
    username: str
    user_ids: List[str]
    video_path: str


class DirectThreadRequest(BaseModel):
    username: str
    thread_id: str
    message: str
