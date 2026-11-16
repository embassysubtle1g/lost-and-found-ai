from fastapi import FastAPI

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
