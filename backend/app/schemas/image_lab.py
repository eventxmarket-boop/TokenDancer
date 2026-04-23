from __future__ import annotations

from typing import Literal

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
