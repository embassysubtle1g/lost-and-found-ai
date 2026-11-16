from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.images import router as images_router
from app.services.model_manager import load_models


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 啟動時載入模型
    model_info = load_models()
    app.state.model_info = model_info

    yield

    # 服務關閉時執行
    print("AI Service is shutting down.")


app = FastAPI(
    title="Lost and Found AI Service",
    description="AI image similarity service powered by DINOv2",
    version="0.1.0",
    lifespan=lifespan,
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
