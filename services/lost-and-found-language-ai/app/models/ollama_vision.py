"""Local quantized Qwen vision backend; keeps the classification API unchanged."""
import base64
from io import BytesIO
from threading import Lock

import httpx
from app.core.config import settings

_generation_lock = Lock()


def generate(image, prompt: str) -> str:
    # Reject concurrent expensive generations instead of consuming extra memory.
    if not _generation_lock.acquire(blocking=False):
        raise RuntimeError("辨識進行中，請等待目前的辨識完成後再試。")
    try:
        photo = image.copy()
        photo.thumbnail((896, 896))
        stream = BytesIO()
        photo.save(stream, format="JPEG", quality=90)
        payload = {
            "model": settings.OLLAMA_MODEL,
            "messages": [{"role": "user", "content": prompt,
                          "images": [base64.b64encode(stream.getvalue()).decode()]}],
            "stream": False,
            "format": "json",
            "keep_alive": "2m",
            "options": {"temperature": 0, "num_ctx": 4096,
                        "num_predict": settings.MAX_NEW_TOKENS},
        }
        try:
            response = httpx.post(settings.OLLAMA_URL.rstrip("/") + "/api/chat",
                                  json=payload, timeout=httpx.Timeout(240, connect=5))
            response.raise_for_status()
            result = response.json()
        except httpx.HTTPError as exc:
            raise RuntimeError("本機 Qwen 辨識服務無法完成請求，請檢查 Ollama 與模型是否就緒。") from exc
        if not result.get("done") or result.get("done_reason") == "length":
            raise RuntimeError("模型輸出未完成，請使用更清楚、單一物品的照片後重試。")
        text = result.get("message", {}).get("content")
        if not isinstance(text, str) or not text.strip():
            raise RuntimeError("模型未回傳物品描述，請稍後再試。")
        return text
    finally:
        _generation_lock.release()
