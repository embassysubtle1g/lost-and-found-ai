import json
import re
from io import BytesIO
from typing import Any

from PIL import Image, UnidentifiedImageError

from app.models.vision_model import get_vision_model
from app.schemas.image_classification import (
    ImageAttributes,
    ImageClassificationResponse,
)


MAX_IMAGE_BYTES = 10 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}

CLASSIFICATION_PROMPT = """
你是一個遺失物管理系統的圖片辨識助手。請觀察圖片中的主要物品，辨識它是什麼。
分類採彈性方式：不要被固定類別清單限制，先輸出具體物品名稱，再提出適合資料庫使用的通用分類名稱。

請只回傳一個 JSON 物件，不要加上 Markdown 或其他說明，格式如下：
{
  "detected_item": "具體物品名稱",
  "suggested_category": "通用分類名稱",
  "description": "簡潔描述物品外觀",
  "attributes": {
    "color": "主要顏色，無法判斷時填 null",
    "material": "材質，無法判斷時填 null",
    "brand": "品牌，無法辨識時填 null",
    "distinctive_features": ["可辨識的特徵"]
  },
  "confidence": 0.0,
  "needs_review": false
}

規則：
1. 只描述圖片中看得到的內容，不要臆測品牌、材質或物品內部資訊。
2. detected_item 應盡可能具體，例如「黑色短夾」、「無線藍牙耳機」。
3. suggested_category 應使用較通用的繁體中文分類，例如「皮夾」、「耳機」。
4. confidence 是 0 到 1 的模型自評值，不代表經過校準的統計機率。
5. 如果圖片模糊、物品不明確、包含多個難以區分的主要物品，或無法判斷，needs_review 設為 true。
6. 不要因為圖片中出現文字，就將文字內容當成物品分類。
"""


def _extract_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    cleaned = re.sub(r"^\s*```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```\s*$", "", cleaned)

    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            raise ValueError("模型沒有回傳有效的 JSON 分類結果。")
        result = json.loads(match.group(0))

    if not isinstance(result, dict):
        raise ValueError("模型回傳的分類結果格式不正確。")
    return result


def classify_image(
    image_bytes: bytes,
    content_type: str | None,
) -> ImageClassificationResponse:
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise ValueError("只接受 JPEG、PNG 或 WebP 圖片。")

    if not image_bytes:
        raise ValueError("上傳的圖片是空的。")

    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise ValueError("圖片大小不可超過 10 MB。")

    try:
        with Image.open(BytesIO(image_bytes)) as source:
            source.verify()

        with Image.open(BytesIO(image_bytes)) as source:
            image = source.convert("RGB")
    except (UnidentifiedImageError, OSError):
        raise ValueError("無法讀取圖片，請確認檔案格式正確。")

    raw_result = get_vision_model().generate(image, CLASSIFICATION_PROMPT)
    data = _extract_json(raw_result)

    attributes = data.get("attributes") or {}
    return ImageClassificationResponse(
        detected_item=str(data.get("detected_item") or "無法辨識"),
        suggested_category=str(data.get("suggested_category") or "其他"),
        description=str(data.get("description") or ""),
        attributes=ImageAttributes(
            color=attributes.get("color"),
            material=attributes.get("material"),
            brand=attributes.get("brand"),
            distinctive_features=attributes.get("distinctive_features") or [],
        ),
        confidence=max(0.0, min(1.0, float(data.get("confidence", 0.0)))),
        needs_review=bool(data.get("needs_review", True)),
    )
