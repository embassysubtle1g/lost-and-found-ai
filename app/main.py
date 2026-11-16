from fastapi import FastAPI
from app.api.v1.images import router as images_router

app = FastAPI(
    title="Lost and Found AI Service",
    description="AI image similarity service powered by DINOv2",
    version="0.1.0",
)


@app.get("/")
def home():
    return {
        "message": "Lost and Found AI Service is running",
        "version": "0.1.0",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }


app.include_router(
    images_router,
    prefix="/api/v1",
)