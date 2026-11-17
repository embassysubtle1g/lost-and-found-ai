import io
import json
import math
import os
import warnings
from contextlib import closing

import boto3
import httpx
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException
from PIL import Image, UnidentifiedImageError

from .db import engine, one, query

LIMIT = 8 * 1024 * 1024
MEDIA_TYPES = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}
MODEL = os.getenv("DINOV2_MODEL", "facebook/dinov2-base")
VERSION = os.getenv("DINOV2_VERSION", "dinov2_vitb14")
Image.MAX_IMAGE_PIXELS = 20_000_000


def validate_image(file):
    data = file.file.read(LIMIT + 1)
    if len(data) > LIMIT:
        raise HTTPException(413, "照片不可超過 8 MB")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as image:
                media_type = MEDIA_TYPES.get(image.format)
                if media_type is None:
                    raise HTTPException(415, "請上傳 JPEG、PNG 或 WebP")
                image.verify()
            with Image.open(io.BytesIO(data)) as image:
                image.load()
    except (ValueError, OSError, UnidentifiedImageError, Image.DecompressionBombError,
            Image.DecompressionBombWarning) as exc:
        raise HTTPException(400, "照片內容無法讀取") from exc
    return data, media_type


def storage():
    return boto3.client("s3", endpoint_url=os.environ["OBJECT_ENDPOINT"],
                        aws_access_key_id=os.environ["OBJECT_ACCESS_KEY"],
                        aws_secret_access_key=os.environ["OBJECT_SECRET_KEY"],
                        region_name="us-east-1",
                        config=Config(connect_timeout=3, read_timeout=10,
                                      s3={"addressing_style": "path"}))


def bucket():
    return os.environ["OBJECT_BUCKET"]


def ensure_bucket():
    with closing(storage()) as client:
        try:
            client.head_bucket(Bucket=bucket())
        except ClientError as exc:
            if exc.response["Error"]["Code"] not in {"404", "NoSuchBucket", "NotFound"}:
                raise
            client.create_bucket(Bucket=bucket())


def get_photo(key):
    with closing(storage()) as client:
        with closing(client.get_object(Bucket=bucket(), Key=key)["Body"]) as stream:
            return stream.read(LIMIT + 1)


def embedding(data, media_type):
    endpoint = os.environ["DINOV2_URL"].rstrip("/") + "/api/v1/images/embedding"
    extension = media_type.split("/")[1].replace("jpeg", "jpg")
    response = httpx.post(endpoint, files={"file": (f"photo.{extension}", data, media_type)},
                          timeout=httpx.Timeout(30, connect=4))
    response.raise_for_status()
    result = response.json()
    if not isinstance(result, dict):
        raise ValueError("DINOv2 回應格式不符")
    values = result.get("embedding")
    if (result.get("status") != "success" or result.get("model") != MODEL
            or result.get("model_version") != VERSION
            or result.get("embedding_dimension") != 768
            or not isinstance(values, list) or len(values) != 768
            or not all(type(value) in (int, float) and math.isfinite(value)
                       and abs(value) <= 1.001 for value in values)
            or not any(values)):
        raise ValueError("DINOv2 模型、向量維度或回應格式與設定不符")
    return json.dumps(values, separators=(",", ":"))


def work_once(lock):
    job = one(lock, """
        UPDATE item_images SET state = 'PROCESSING'
        WHERE id = (
            SELECT id FROM item_images
            WHERE state = 'PENDING' AND removed_at IS NULL ORDER BY id LIMIT 1
            FOR UPDATE SKIP LOCKED
        )
        RETURNING id, object_key, media_type
    """)
    lock.commit()
    if job:
        try:
            vector = embedding(get_photo(job.object_key), job.media_type)
        except (httpx.HTTPError, BotoCoreError, ClientError, OSError, TypeError, ValueError) as exc:
            query(lock, """
                UPDATE item_images SET state = 'FAILED', error = :error
                WHERE id = :id AND removed_at IS NULL
            """, id=job.id, error=f"{type(exc).__name__}: {exc}"[:400])
        else:
            query(lock, """
                UPDATE item_images SET state = 'COMPLETED', error = NULL, model = :model,
                    model_version = :version, embedding = CAST(:vector AS vector)
                WHERE id = :id AND removed_at IS NULL
            """, id=job.id, model=MODEL, version=VERSION, vector=vector)
        lock.commit()
    removed = one(lock, """
        SELECT id, object_key FROM item_images WHERE removed_at IS NOT NULL ORDER BY id LIMIT 1
    """)
    if removed:
        with closing(storage()) as client:
            client.delete_object(Bucket=bucket(), Key=removed.object_key)
        query(lock, "DELETE FROM item_images WHERE id = :id AND removed_at IS NOT NULL",
              id=removed.id)
    lock.commit()
    return bool(job or removed)


def run_worker(stop):
    import logging

    logger = logging.getLogger(__name__)
    while not stop.is_set():
        try:
            with engine.connect() as lock:
                acquired = one(lock, "SELECT pg_try_advisory_lock(410394) AS acquired")
                try:
                    if not acquired.acquired:
                        stop.wait(2)
                        continue
                    query(lock, """
                        UPDATE item_images SET state = 'PENDING'
                        WHERE state = 'PROCESSING' AND removed_at IS NULL
                    """)
                    lock.commit()
                    while not stop.is_set():
                        if not work_once(lock):
                            stop.wait(1)
                finally:
                    lock.rollback()
                    if acquired.acquired and not lock.invalidated:
                        query(lock, "SELECT pg_advisory_unlock(410394)")
                        lock.commit()
        except Exception:
            logger.exception("照片處理暫停，稍後重試")
            stop.wait(3)
