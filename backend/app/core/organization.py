from fastapi import Header, HTTPException

from .db import engine, one


def organization_context(organization_id: int | None = Header(None, alias="X-Organization-ID", ge=1)):
    """Select the organization whose records are being managed."""
    with engine.connect() as connection:
        if organization_id is None:
            organization = one(connection, "SELECT id FROM organizations ORDER BY id LIMIT 1")
        else:
            organization = one(connection, "SELECT id FROM organizations WHERE id = :id", id=organization_id)
    if organization is None:
        raise HTTPException(409, "請先建立或選擇保管機構")
    return {"organization_id": organization.id}
