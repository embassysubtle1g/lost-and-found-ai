import os

import httpx
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, ValidationError


class Attributes(BaseModel):
    color: str | None = None
    material: str | None = None
    brand: str | None = None
    distinctive_features: list[str] = Field(default_factory=list)


class Classification(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)
    detected_item: str = Field(min_length=1, max_length=120)
    suggested_category: str = Field(min_length=1, max_length=80)
    description: str = Field(max_length=2000)
    attributes: Attributes
    confidence: float = Field(ge=0, le=1)
    needs_review: bool


def classify_photo(data: bytes, media_type: str):
    endpoint = os.getenv("LANGUAGE_AI_URL", "http://127.0.0.1:8081").rstrip("/")
    timeout = float(os.getenv("LANGUAGE_AI_TIMEOUT", "300"))
    extension = media_type.split("/")[1]
    try:
        response = httpx.post(
            endpoint + "/api/v1/images/classify",
            files={"file": (f"photo.{extension}", data, media_type)},
            timeout=httpx.Timeout(timeout, connect=5),
        )
        response.raise_for_status()
    except httpx.TimeoutException as exc:
        raise HTTPException(504, "物品描述逾時，模型可能仍在載入；可稍後重試或手動填寫") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(503, "物品描述服務暫時無法使用，可手動填寫後登記") from exc
    try:
        result = Classification.model_validate(response.json())
    except (ValueError, ValidationError) as exc:
        raise HTTPException(502, "物品描述服務回傳格式不符，請稍後重試") from exc
    tags = result.attributes.distinctive_features[:]
    for value in (result.attributes.material, result.attributes.brand):
        if value and value not in tags:
            tags.append(value)
    return {
        "title": result.detected_item, "category": result.suggested_category,
        "description": result.description, "color": result.attributes.color or "",
        "tags": list(dict.fromkeys(tags))[:30], "confidence": result.confidence,
        "needs_review": result.needs_review, "attributes": result.attributes.model_dump(),
    }
