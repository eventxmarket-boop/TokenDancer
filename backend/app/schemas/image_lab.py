from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


AllowedImageSize = Literal["1024x1024", "1024x1536", "1536x1024", "auto"]
AllowedImageQuality = Literal["low", "medium", "high", "auto"]
AllowedImageFormat = Literal["png", "webp", "jpeg"]


class ImageGenerateRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=4000)
    size: AllowedImageSize = "1024x1024"
    quality: AllowedImageQuality = "medium"
    output_format: AllowedImageFormat = "png"


class ImageGenerateResponse(BaseModel):
    image_base64: str
    mime_type: str
    model: str
    size: str
    quality: str
    output_format: str


class PlusBridgeSubmitRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=4000)
    size: AllowedImageSize = "1024x1024"
    quality: AllowedImageQuality = "medium"
    output_format: AllowedImageFormat = "png"
    image_base64: str = Field(min_length=1)
    mime_type: str = "image/png"
    model: str = "chatgpt-plus-bridge"
    transport: str = "persistent"
    source: str = "chatgpt-plus"
    user_id: Optional[str] = None


class PlusBridgeSubmitResponse(BaseModel):
    accepted: bool
    received_at: str
    prompt: str
    size: str
    quality: str
    output_format: str
    image_base64: str
    mime_type: str
    model: str
    transport: str = "persistent"
    source: str
    user_id: Optional[str] = None
