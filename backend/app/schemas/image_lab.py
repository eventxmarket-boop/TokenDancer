from __future__ import annotations

from typing import Any, Literal, Optional

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


class PlusBridgeEventRequest(BaseModel):
    stage: str = Field(min_length=1, max_length=64)
    message: str = Field(default="", max_length=500)
    mode: str = Field(default="generate", max_length=32)
    transport: str = Field(default="persistent", max_length=32)
    prompt: str = Field(default="", max_length=4000)
    prompt_length: int = 0
    size: str = Field(default="unknown", max_length=32)
    quality: str = Field(default="unknown", max_length=32)
    output_format: str = Field(default="png", max_length=32)
    success: bool | None = None
    error: str | None = Field(default=None, max_length=1000)
    user_id: Optional[str] = None


class PlusBridgeEventResponse(BaseModel):
    accepted: bool
    received_at: str
    stage: str
    message: str
    mode: str
    transport: str
    prompt_length: int
    size: str
    quality: str
    output_format: str
    success: bool | None = None
    error: str | None = None
    user_id: Optional[str] = None


class PlusBridgeStatusResponse(BaseModel):
    updated_at: str | None = None
    mode: str = "generate"
    transport: str = "persistent"
    stage: str = "idle"
    message: str = ""
    prompt: str = ""
    prompt_length: int = 0
    size: str = "unknown"
    quality: str = "unknown"
    output_format: str = "png"
    model: str = "chatgpt-plus-bridge"
    page_url: str = ""
    image_base64: str = ""
    mime_type: str = ""
    success: bool | None = None
    error: str | None = None
    user_id: Optional[str] = None
    events: list[dict[str, Any]] = Field(default_factory=list)
