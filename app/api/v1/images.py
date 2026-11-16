from fastapi import APIRouter, UploadFile, File, HTTPException
from PIL import Image, UnidentifiedImageError
from io import BytesIO

router = APIRouter(
    prefix="/images",
    tags=["Images"],
)


@router.post("/inspect")
async def inspect_image(file: UploadFile = File(...)):

    allowed_types = [
        "image/jpeg",
        "image/png",
        "image/webp",
    ]

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Unsupported image format",
        )

    image_bytes = await file.read()

    try:
        image = Image.open(BytesIO(image_bytes))
        image.verify()

    except (UnidentifiedImageError, OSError):
        raise HTTPException(
            status_code=400,
            detail="Invalid image file",
        )

    image = Image.open(BytesIO(image_bytes))

    return {
        "filename": file.filename,
        "format": image.format,
        "width": image.width,
        "height": image.height,
        "status": "success",
    }