from contextlib import asynccontextmanager
from pathlib import Path
from threading import Event, Thread

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .api import auth, items
from .services.media import ensure_bucket, run_worker

DEMO = Path(__file__).resolve().parent / "api" / "demo"


@asynccontextmanager
async def lifespan(app):
    ensure_bucket()
    stop = Event()
    worker = Thread(target=run_worker, args=(stop,), daemon=True)
    worker.start()
    try:
        yield
    finally:
        stop.set()
        worker.join(timeout=2)


app = FastAPI(title="拾獲物招領 API", lifespan=lifespan)
app.include_router(auth.router, prefix="/api/v1")
app.include_router(items.router, prefix="/api/v1")
app.mount("/assets", StaticFiles(directory=DEMO), name="assets")


@app.get("/", include_in_schema=False)
@app.get("/staff", include_in_schema=False)
def demo():
    return FileResponse(DEMO / "index.html")


@app.get("/health")
def health():
    return {"status": "ok"}
