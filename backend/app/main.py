from contextlib import asynccontextmanager
from pathlib import Path
from threading import Event, Thread

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from .api import items, radar, locations, reporting_units
from .services.media import ensure_bucket, run_worker

FRONTEND = Path(__file__).resolve().parents[2] / "frontend" / "dist"


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


app = FastAPI(title="尋物雷達 API", lifespan=lifespan)
app.include_router(items.router, prefix="/api/v1")
app.include_router(radar.router, prefix="/api")
app.include_router(locations.router, prefix="/api")
app.include_router(reporting_units.router, prefix="/api")
app.mount("/assets", StaticFiles(directory=FRONTEND / "assets", check_dir=False), name="assets")


@app.get("/", include_in_schema=False)
@app.get("/staff", include_in_schema=False)
def frontend():
    if not (FRONTEND / "index.html").is_file():
        return HTMLResponse(
            "<!doctype html><html lang='zh-Hant'><meta charset='utf-8'>"
            "<title>尋物雷達</title><h1>請先建置新版前端</h1>"
            "<p>在專案根目錄執行 npm --prefix frontend ci，"
            "再執行 npm --prefix frontend run build，完成後重新整理。</p></html>",
            status_code=503,
        )
    return FileResponse(FRONTEND / "index.html")


@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/radar.html", include_in_schema=False)
def radar_page():
    if not (FRONTEND / "radar.html").is_file():
        return frontend()
    return FileResponse(FRONTEND / "radar.html")
