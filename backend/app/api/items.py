import uuid
from contextlib import closing
from datetime import date

import httpx
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile

from ..core.db import engine, one, query, rows
from ..core.organization import organization_context
from ..schemas.organizations import OrganizationData
from ..models.items import images, owned
from ..schemas.items import ItemData
from ..services.media import MODEL, VERSION, bucket, embedding, get_photo, storage, validate_image

router = APIRouter(tags=["items"])
PUBLIC_FIELDS = """
    i.id, i.reference, i.name, i.category, i.found_date, i.found_location, i.found_region,
    o.id AS organization_id, o.name AS organization_name,
    o.address AS organization_address, o.phone AS organization_phone,
    (SELECT id FROM item_images WHERE item_id = i.id AND is_cover
     AND removed_at IS NULL) AS cover_id
"""
PUBLIC_FROM = "FROM items i JOIN organizations o ON o.id = i.organization_id"
FILTERS = """
    i.status = 'AVAILABLE'
    AND (:keyword = '' OR i.name ILIKE :keyword_pattern OR i.reference ILIKE :keyword_pattern)
    AND (:category = '' OR i.category = :category)
    AND (:location = '' OR i.found_region ILIKE :location_pattern
         OR (i.found_region = '' AND i.found_location ILIKE :location_pattern))
    AND (CAST(:lost_date AS date) IS NULL OR i.found_date >= CAST(:lost_date AS date))
    AND (:organization = 0 OR i.organization_id = :organization)
    AND (CAST(:since AS date) IS NULL OR i.found_date >= CAST(:since AS date))
    AND (CAST(:until AS date) IS NULL OR i.found_date <= CAST(:until AS date))
"""


def public_filters(keyword, category, location, organization, since, until, lost_date=None):
    if since and until and since > until:
        raise HTTPException(422, "起始日期不可晚於結束日期")
    return dict(keyword=keyword, keyword_pattern=f"%{keyword}%", category=category,
                location=location, location_pattern=f"%{location}%",
                organization=organization, since=since, until=until, lost_date=lost_date)


@router.get("/public/organizations")
def organizations():
    with engine.connect() as connection:
        return rows(connection, "SELECT id, name, address, phone FROM organizations ORDER BY name")



@router.post("/staff/organizations", status_code=201)
def create_organization(data: OrganizationData):
    from sqlalchemy.exc import IntegrityError

    try:
        with engine.begin() as connection:
            organization = one(connection, """
                INSERT INTO organizations(name, address, phone) VALUES (:name, :address, :phone)
                RETURNING id, name, address, phone
            """, **data.model_dump())
    except IntegrityError as exc:
        raise HTTPException(409, "機構名稱已存在") from exc
    return dict(organization)


@router.put("/staff/organization")
def update_organization(data: OrganizationData, organization=Depends(organization_context)):
    from sqlalchemy.exc import IntegrityError

    try:
        with engine.begin() as connection:
            result = one(connection, """
                UPDATE organizations SET name = :name, address = :address, phone = :phone
                WHERE id = :id RETURNING id, name, address, phone
            """, id=organization["organization_id"], **data.model_dump())
    except IntegrityError as exc:
        raise HTTPException(409, "機構名稱已存在") from exc
    return dict(result)


@router.get("/public/items")
def public_items(keyword: str = Query("", max_length=120), category: str = Query("", max_length=80),
                 location: str = Query("", max_length=240), organization: int = Query(0, ge=0),
                 since: date | None = None, until: date | None = None, lost_date: date | None = None,
                 page: int = Query(1, ge=1, le=100000), limit: int = Query(20, ge=1, le=50)):
    filters = public_filters(keyword, category, location, organization, since, until, lost_date)
    with engine.connect() as connection:
        result = rows(connection, f"""
            SELECT {PUBLIC_FIELDS} {PUBLIC_FROM} WHERE {FILTERS}
            ORDER BY i.id DESC LIMIT :limit OFFSET :offset
        """, **filters, limit=limit + 1, offset=(page - 1) * limit)
    return {"items": result[:limit], "page": page, "has_more": len(result) > limit}


@router.get("/public/items/{item_id}")
def public_item(item_id: int):
    with engine.connect() as connection:
        item = one(connection, f"""
            SELECT {PUBLIC_FIELDS} {PUBLIC_FROM} WHERE i.id = :id AND i.status = 'AVAILABLE'
        """, id=item_id)
        if item is None:
            raise HTTPException(404, "找不到待認領物品")
        return {**item, "images": images(connection, item_id)}


@router.post("/public/search")
def search(file: UploadFile = File(), keyword: str = Form("", max_length=120), category: str = Form("", max_length=80),
           location: str = Form("", max_length=240), organization: int = Form(0, ge=0),
           since: date | None = Form(None), until: date | None = Form(None),
           lost_date: date | None = Form(None),
           limit: int = Form(12, ge=1, le=30)):
    filters = public_filters(keyword, category, location, organization, since, until, lost_date)
    data, media_type = validate_image(file)
    try:
        vector = embedding(data, media_type)
    except (httpx.HTTPError, ValueError, TypeError) as exc:
        raise HTTPException(503, "照片搜尋暫時無法使用，請稍後重試") from exc
    with engine.connect() as connection:
        return {"items": rows(connection, f"""
            SELECT {PUBLIC_FIELDS}, 1 - best.distance AS similarity
            {PUBLIC_FROM}
            JOIN (
                SELECT item_id, MIN(embedding <=> CAST(:vector AS vector)) AS distance
                FROM item_images WHERE removed_at IS NULL AND state = 'COMPLETED'
                  AND model = :model AND model_version = :version GROUP BY item_id
            ) best ON best.item_id = i.id
            WHERE {FILTERS} ORDER BY best.distance, i.id DESC LIMIT :limit
        """, **filters, vector=vector, model=MODEL, version=VERSION, limit=limit)}


@router.get("/staff/items")
def staff_items(page: int = Query(1, ge=1, le=100000), limit: int = Query(20, ge=1, le=50),
                staff=Depends(organization_context)):
    with engine.connect() as connection:
        result = rows(connection, """
            SELECT id, reference, name, category, found_date, found_location, found_region, status, returned_at
            FROM items WHERE organization_id = :org ORDER BY id DESC LIMIT :limit OFFSET :offset
        """, org=staff["organization_id"], limit=limit + 1, offset=(page - 1) * limit)
    return {"items": result[:limit], "page": page, "has_more": len(result) > limit}


@router.post("/staff/items", status_code=201)
def create_item(data: ItemData, staff=Depends(organization_context)):
    with engine.begin() as connection:
        item = one(connection, """
            INSERT INTO items(reference, organization_id, name, category, found_date,
                              found_location, found_region, private_note)
            VALUES (:reference, :org, :name, :category, :found_date, :found_location, :found_region, :private_note)
            RETURNING *
        """, reference=uuid.uuid4().hex.upper(), org=staff["organization_id"], **data.model_dump())
    return dict(item)


@router.get("/staff/items/{item_id}")
def staff_item(item_id: int, staff=Depends(organization_context)):
    with engine.connect() as connection:
        return {**owned(connection, item_id, staff), "images": images(connection, item_id, True)}


@router.put("/staff/items/{item_id}")
def edit_item(item_id: int, data: ItemData, staff=Depends(organization_context)):
    with engine.begin() as connection:
        owned(connection, item_id, staff, lock=True)
        item = one(connection, """
            UPDATE items SET name = :name, category = :category, found_date = :found_date,
                found_location = :found_location, found_region = :found_region, private_note = :private_note
            WHERE id = :id RETURNING *
        """, id=item_id, **data.model_dump())
    return dict(item)


@router.post("/staff/items/{item_id}/return")
def return_item(item_id: int, staff=Depends(organization_context)):
    with engine.begin() as connection:
        item = owned(connection, item_id, staff, lock=True)
        if item["status"] == "RETURNED":
            return item
        if item["status"] != "AVAILABLE":
            raise HTTPException(409, "只有待認領物品可以登記歸還")
        return dict(one(connection, """
            UPDATE items SET status = 'RETURNED', returned_at = now(), returned_by = NULL
            WHERE id = :id RETURNING *
        """, id=item_id))


@router.post("/staff/items/{item_id}/withdraw", status_code=204)
def withdraw_item(item_id: int, staff=Depends(organization_context)):
    with engine.begin() as connection:
        item = owned(connection, item_id, staff, lock=True)
        if item["status"] == "RETURNED":
            raise HTTPException(409, "已歸還物品須保留歸還紀錄")
        query(connection, "UPDATE items SET status = 'WITHDRAWN' WHERE id = :id", id=item_id)
    return Response(status_code=204)


@router.post("/staff/items/{item_id}/images", status_code=201)
def upload_image(item_id: int, file: UploadFile = File(), staff=Depends(organization_context)):
    with engine.connect() as connection:
        owned(connection, item_id, staff)
    data, media_type = validate_image(file)
    key = f"items/{item_id}/{uuid.uuid4().hex}"
    with closing(storage()) as client:
        try:
            client.put_object(Bucket=bucket(), Key=key, Body=data, ContentType=media_type)
        except (BotoCoreError, ClientError) as exc:
            raise HTTPException(503, "照片儲存服務暫時無法使用") from exc
        try:
            with engine.begin() as connection:
                item = owned(connection, item_id, staff, lock=True)
                if item["status"] != "AVAILABLE":
                    raise HTTPException(409, "只有待認領物品可以新增照片")
                existing = images(connection, item_id)
                if len(existing) >= 8:
                    raise HTTPException(409, "每件物品最多八張照片")
                photo = one(connection, """
                    INSERT INTO item_images(item_id, object_key, media_type, size_bytes, is_cover)
                    VALUES (:item, :key, :media, :size, :cover)
                    RETURNING id, is_cover, state
                """, item=item_id, key=key, media=media_type, size=len(data), cover=not existing)
        except HTTPException:
            # A business-rule rejection happens before the database commit.
            client.delete_object(Bucket=bucket(), Key=key)
            raise
    return dict(photo)


def owned_photo(connection, item_id, image_id, staff):
    owned(connection, item_id, staff, lock=True)
    photo = one(connection, """
        SELECT id, is_cover, state FROM item_images
        WHERE id = :id AND item_id = :item AND removed_at IS NULL
    """, id=image_id, item=item_id)
    if photo is None:
        raise HTTPException(404, "找不到照片")
    return photo


@router.put("/staff/items/{item_id}/images/{image_id}/cover", status_code=204)
def set_cover(item_id: int, image_id: int, staff=Depends(organization_context)):
    with engine.begin() as connection:
        owned_photo(connection, item_id, image_id, staff)
        query(connection, "UPDATE item_images SET is_cover = false WHERE item_id = :item AND is_cover",
              item=item_id)
        query(connection, "UPDATE item_images SET is_cover = true WHERE id = :id", id=image_id)
    return Response(status_code=204)


@router.delete("/staff/items/{item_id}/images/{image_id}", status_code=204)
def remove_image(item_id: int, image_id: int, staff=Depends(organization_context)):
    with engine.begin() as connection:
        photo = owned_photo(connection, item_id, image_id, staff)
        query(connection, """
            UPDATE item_images SET removed_at = now(), is_cover = false WHERE id = :id
        """, id=image_id)
        if photo.is_cover:
            query(connection, """
                UPDATE item_images SET is_cover = true WHERE id = (
                    SELECT id FROM item_images WHERE item_id = :item AND removed_at IS NULL
                    ORDER BY id LIMIT 1
                )
            """, item=item_id)
    return Response(status_code=204)


@router.post("/staff/items/{item_id}/images/{image_id}/retry", status_code=204)
def retry_image(item_id: int, image_id: int, staff=Depends(organization_context)):
    with engine.begin() as connection:
        owned_photo(connection, item_id, image_id, staff)
        result = query(connection, """
            UPDATE item_images SET state = 'PENDING', error = NULL
            WHERE id = :id AND state = 'FAILED'
        """, id=image_id)
        if result.rowcount == 0:
            raise HTTPException(409, "只有失敗的照片可以重試")
    return Response(status_code=204)


def photo_response(image_id, organization_id=None):
    with engine.connect() as connection:
        photo = one(connection, """
            SELECT p.object_key, p.media_type FROM item_images p
            JOIN items i ON i.id = p.item_id
            WHERE p.id = :id AND p.removed_at IS NULL AND
        """ + (" i.status = 'AVAILABLE'" if organization_id is None else " i.organization_id = :org"),
                    id=image_id, org=organization_id)
        if photo is None:
            raise HTTPException(404, "找不到照片")
    try:
        data = get_photo(photo.object_key)
    except (BotoCoreError, ClientError) as exc:
        raise HTTPException(503, "照片暫時無法讀取") from exc
    return Response(data, media_type=photo.media_type,
                    headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})


@router.get("/public/images/{image_id}", responses={200: {"content": {"image/*": {}}}})
def public_photo(image_id: int):
    return photo_response(image_id)


@router.get("/staff/images/{image_id}", responses={200: {"content": {"image/*": {}}}})
def staff_photo(image_id: int, staff=Depends(organization_context)):
    return photo_response(image_id, staff["organization_id"])
