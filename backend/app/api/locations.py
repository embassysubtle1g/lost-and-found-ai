from fastapi import APIRouter, HTTPException
from ..core.db import engine, rows, one

router = APIRouter(tags=["Campus locations"])

@router.get("/locations")
def list_locations():
    with engine.connect() as connection:
        return rows(connection, """SELECT id, name, zone, map_x AS x, map_y AS y,
            label_x AS "labelX", label_y AS "labelY", aliases
            FROM campus_locations ORDER BY sort_order, id""")

def resolve_location(connection, location_id, name):
    if location_id:
        location = one(connection, "SELECT id, name, aliases FROM campus_locations WHERE id = :id", id=location_id)
        if not location:
            raise HTTPException(422, "找不到指定的校園地點")
        if name != location["name"] and name not in location["aliases"]:
            raise HTTPException(422, "地點名稱與地點編號不一致")
        return location
    return one(connection, """SELECT id, name, aliases FROM campus_locations
        WHERE name = :name OR aliases ? :name ORDER BY id LIMIT 1""", name=name)
