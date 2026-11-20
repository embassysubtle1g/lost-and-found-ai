import logging

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.image_classification import ImageClassificationResponse
from app.services.image_classification import classify_image

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/images", tags=["Images"])


@router.post(
    "/classify",
    response_model=ImageClassificationResponse,
    summary="辨識並分類遺失物圖片",
)
def classify_lost_item_image(
    file: UploadFile = File(...),
) -> ImageClassificationResponse:
    try:
        image_bytes = file.file.read()
        return classify_image(image_bytes, file.content_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.exception("圖片分類時發生執行錯誤")
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("圖片分類時發生未預期錯誤")
        raise HTTPException(
            status_code=500,
            detail="圖片分類失敗，請稍後再試。",
        ) from exc
