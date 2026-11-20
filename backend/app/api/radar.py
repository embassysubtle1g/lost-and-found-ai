import base64
import binascii
import io
import json
import uuid
from contextlib import closing
from datetime import datetime
from typing import Literal

import httpx
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field, ConfigDict
from starlette.datastructures import UploadFile

from ..core.db import engine, one, rows, query
from ..services.media import bucket, storage, validate_image, embedding, get_photo

from ..services.language_ai import classify_photo

router = APIRouter(tags=["Radar"])


class Report(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    record_type: Literal["LOST", "FOUND"]
    title: str = Field(min_length=1, max_length=120)
    category: str = Field(min_length=1, max_length=80)
    color: str = Field(default="", max_length=80)
    tags: list[str] = Field(default_factory=list, max_length=30)
    location: str = Field(min_length=1, max_length=120)
    location_detail: str = Field(default="", max_length=120)
    datetime: datetime
    description: str = Field(default="", max_length=2000)
    user_name: str = Field(min_length=1, max_length=120)
    user_contact: str = Field(min_length=1, max_length=240)
    image_url: str = Field(default="", max_length=12_000_000)


class Recognition(BaseModel):
    image: str = Field(max_length=12_000_000)


class Pair(BaseModel):
    lost_id: str
    found_id: str


def read_data_image(value):
    try:
        header, encoded = value.split(",", 1)
        if header not in {"data:image/jpeg;base64", "data:image/png;base64", "data:image/webp;base64"}:
            raise ValueError()
        data = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise HTTPException(400, "請上傳 JPEG、PNG 或 WebP 圖片") from exc
    return validate_image(UploadFile(filename="photo", file=io.BytesIO(data)))


def serialize(item):
    data = dict(item["radar_data"] or {})
    data.update({
        "item_id": item["reference"], "record_type": item["record_type"],
        "status": "OPEN" if item["status"] == "AVAILABLE" else "MATCHED",
        "title": item["name"], "category": item["category"],
        "location": item["found_region"] or item["found_location"],
        "location_detail": data.get("location_detail", item["found_location"]),
        "datetime": data.get("datetime", str(item["found_date"])).replace("T", " "),
        "color": data.get("color", ""), "tags": data.get("tags", []),
        "description": data.get("description", ""),
        "user_name": data.get("user_name", item["organization_name"]),
        "user_contact": data.get("user_contact", item["organization_phone"]),
        "image_url": f"/api/images/{item['cover_id']}" if item["cover_id"] else "",
    })
    return data


SELECT = """
    SELECT i.*, o.name AS organization_name, o.phone AS organization_phone,
        (SELECT p.id FROM item_images p WHERE p.item_id = i.id AND p.is_cover
         AND p.removed_at IS NULL) AS cover_id
    FROM items i JOIN organizations o ON o.id = i.organization_id
"""


@router.get("/items")
def list_reports():
    with engine.connect() as connection:
        return [serialize(item) for item in rows(connection, SELECT + " ORDER BY i.id DESC")]


@router.post("/items", status_code=201)
def create_report(data: Report):
    photo = read_data_image(data.image_url) if data.image_url else None
    key = "radar/" + uuid.uuid4().hex
    if photo:
        try:
            with closing(storage()) as client:
                client.put_object(Bucket=bucket(), Key=key, Body=photo[0], ContentType=photo[1])
        except (BotoCoreError, ClientError) as exc:
            raise HTTPException(503, "圖片儲存暫時無法使用") from exc
    payload = data.model_dump(mode="json", exclude={"image_url"})
    with engine.begin() as connection:
        organization = one(connection, """
            INSERT INTO organizations(name, address, phone)
            VALUES (:name, :address, :phone)
            ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name RETURNING id
        """, name=data.user_name, address=data.location, phone=data.user_contact)
        item = one(connection, """
            INSERT INTO items(reference, organization_id, name, category, found_date,
                found_location, found_region, record_type, radar_data)
            VALUES (:reference, :organization, :title, :category, :day, :place, :region,
                :record_type, CAST(:payload AS jsonb)) RETURNING id
        """, reference=data.record_type + "-" + uuid.uuid4().hex[:16].upper(),
                   organization=organization.id, title=data.title, category=data.category,
                   day=data.datetime.date(), place=data.location_detail or data.location,
                   region=data.location, record_type=data.record_type, payload=json.dumps(payload))
        if photo:
            query(connection, """
                INSERT INTO item_images(item_id, object_key, media_type, size_bytes, is_cover)
                VALUES (:id, :key, :media, :size, true)
            """, id=item.id, key=key, media=photo[1], size=len(photo[0]))
        result = one(connection, SELECT + " WHERE i.id = :id", id=item.id)
    return serialize(result)


@router.post("/ai-recognize")
def recognize(data: Recognition):
    photo, media_type = read_data_image(data.image)
    return classify_photo(photo, media_type)


def matches(connection):
    reports = rows(connection, SELECT + " WHERE i.status = 'AVAILABLE'")
    vectors = rows(connection, """
        SELECT l.item_id AS lost_id, f.item_id AS found_id,
               MAX(1 - (l.embedding <=> f.embedding)) AS similarity
        FROM item_images l
        JOIN items li ON li.id = l.item_id AND li.record_type = 'LOST' AND li.status = 'AVAILABLE'
        JOIN item_images f ON f.state = 'COMPLETED' AND f.removed_at IS NULL
                             AND f.model = l.model AND f.model_version = l.model_version
        JOIN items fi ON fi.id = f.item_id AND fi.record_type = 'FOUND' AND fi.status = 'AVAILABLE'
        WHERE l.state = 'COMPLETED' AND l.removed_at IS NULL
        GROUP BY l.item_id, f.item_id
    """)
    distances = {(pair["lost_id"], pair["found_id"]): float(pair["similarity"]) for pair in vectors}
    dismissed = {(pair["lost_id"], pair["found_id"]) for pair in rows(connection, "SELECT * FROM dismissed_matches")}
    result = []
    for lost in reports:
        if lost["record_type"] != "LOST":
            continue
        for found in reports:
            pair = (lost["id"], found["id"])
            if found["record_type"] != "FOUND" or pair in dismissed:
                continue
            left, right = serialize(lost), serialize(found)
            score, reasons = 0, []
            if left["category"] == right["category"]:
                score += 40
                reasons.append("類別一致")
            if left["color"] and right["color"] and (
                left["color"] in right["color"] or right["color"] in left["color"]
            ):
                score += 25
                reasons.append("顏色相近")
            if left["location"] == right["location"]:
                score += 20
                reasons.append("地點相符")
            overlap = [tag for tag in left["tags"] if tag and any(
                tag in other or other in tag for other in right["tags"] if other
            )]
            if overlap:
                score += min(15, len(overlap) * 8)
                reasons.append("特徵標籤吻合")
            if pair in distances:
                score = max(0, min(100, distances[pair] * 100))
                reasons.insert(0, "DINOv2 圖片向量相似度")
            else:
                reasons.insert(0, "依填寫資料比對，圖片向量尚未就緒")
            if score >= 60:
                result.append({"match_id": left["item_id"] + "_" + right["item_id"],
                               "similarity": round(min(99, score), 1), "reasons": reasons,
                               "lost_item": left, "found_item": right})
    return sorted(result, key=lambda pair: pair["similarity"], reverse=True)


@router.get("/matches")
def list_matches():
    with engine.connect() as connection:
        return matches(connection)


def pair_records(connection, data, lock=False):
    items = rows(connection, """
        SELECT id, reference, record_type, status FROM items
        WHERE reference IN (:lost, :found) ORDER BY id
    """ + (" FOR UPDATE" if lock else ""), lost=data.lost_id, found=data.found_id)
    by_reference = {item["reference"]: item for item in items}
    lost, found = by_reference.get(data.lost_id), by_reference.get(data.found_id)
    if not lost or not found or lost["record_type"] != "LOST" or found["record_type"] != "FOUND":
        raise HTTPException(404, "找不到有效的遺失與拾獲配對")
    return lost, found


@router.post("/matches/confirm", status_code=204)
def confirm(data: Pair):
    with engine.begin() as connection:
        lost, found = pair_records(connection, data, lock=True)
        if lost["status"] == found["status"] == "RETURNED":
            return Response(status_code=204)
        if lost["status"] != "AVAILABLE" or found["status"] != "AVAILABLE":
            raise HTTPException(409, "此物品已結案")
        query(connection, """
            UPDATE items SET status = 'RETURNED', returned_at = now(), returned_by = NULL
            WHERE id IN (:lost, :found)
        """, lost=lost["id"], found=found["id"])
    return Response(status_code=204)


@router.post("/matches/dismiss", status_code=204)
def dismiss(data: Pair):
    with engine.begin() as connection:
        lost, found = pair_records(connection, data)
        query(connection, """
            INSERT INTO dismissed_matches(lost_id, found_id) VALUES (:lost, :found)
            ON CONFLICT DO NOTHING
        """, lost=lost["id"], found=found["id"])
    return Response(status_code=204)


@router.delete("/matches/dismissed", status_code=204)
def reset_matches():
    with engine.begin() as connection:
        query(connection, "DELETE FROM dismissed_matches")
        query(connection, """
            UPDATE item_images SET state = 'PENDING', error = NULL
            WHERE state = 'FAILED' AND removed_at IS NULL
        """)
    return Response(status_code=204)

@router.get("/images/{image_id}")
def report_photo(image_id: int):
    with engine.connect() as connection:
        photo = one(connection, """
            SELECT object_key, media_type FROM item_images
            WHERE id = :id AND removed_at IS NULL
        """, id=image_id)
    if photo is None:
        raise HTTPException(404, "找不到照片")
    try:
        data = get_photo(photo.object_key)
    except (BotoCoreError, ClientError) as exc:
        raise HTTPException(503, "照片暫時無法讀取") from exc
    return Response(data, media_type=photo.media_type,
                    headers={"X-Content-Type-Options": "nosniff", "Cache-Control": "no-store"})
