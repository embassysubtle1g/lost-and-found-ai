from fastapi import HTTPException

from ..core.db import one, rows


def owned(connection, item_id, staff, lock=False):
    item = one(connection, """
        SELECT * FROM items WHERE id = :id AND organization_id = :org
    """ + (" FOR UPDATE" if lock else ""), id=item_id, org=staff["organization_id"])
    if item is None:
        raise HTTPException(404, "找不到物品")
    return dict(item)


def images(connection, item_id, private=False):
    fields = "id, is_cover, media_type"
    if private:
        fields += ", size_bytes, state, error, model, model_version"
    return rows(connection, f"""
        SELECT {fields} FROM item_images WHERE item_id = :id AND removed_at IS NULL
        ORDER BY is_cover DESC, id
    """, id=item_id)
