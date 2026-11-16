from io import BytesIO

from fastapi import APIRouter, UploadFile, File, HTTPException
from PIL import Image, UnidentifiedImageError

from app.services.model_manager import embedding_service
from app.schemas.embedding import EmbeddingResponse


router = APIRouter(
    prefix="/images",
    tags=["Images"],
)


ALLOWED_TYPES = [
    "image/jpeg",
    "image/png",
    "image/webp",
]


async def read_image(file: UploadFile):
    """讀取並驗證上傳圖片"""

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported image format",
        )

    image_bytes = await file.read()

    if not image_bytes:
        raise HTTPException(
            status_code=400,
            detail="Empty image file",
        )

    try:
        image = Image.open(BytesIO(image_bytes))
        image.verify()

        image = Image.open(BytesIO(image_bytes))
        image.load()

        return image

    except (UnidentifiedImageError, OSError):
        raise HTTPException(
            status_code=400,
            detail="Invalid image file",
        )


@router.post("/inspect")
async def inspect_image(file: UploadFile = File(...)):
    """檢查上傳圖片"""

    image = await read_image(file)

    return {
        "filename": file.filename,
        "format": image.format,
        "width": image.width,
        "height": image.height,
        "status": "success",
    }


@router.post(
    "/embedding",
    response_model=EmbeddingResponse,
)
async def generate_embedding(file: UploadFile = File(...)):
    """將上傳圖片轉換成 DINOv2 特徵向量"""

    image = await read_image(file)

    try:
        embedding = embedding_service.extract_embedding(image)
        model_info = embedding_service.get_model_info()

    except RuntimeError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        )

    return {
        "status": "success",
        "filename": file.filename or "unknown",
        "model": model_info["model_id"],
        "model_version": model_info["model"],
        "embedding_dimension": len(embedding),
        "embedding": embedding,
    }
