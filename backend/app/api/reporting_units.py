from fastapi import APIRouter, HTTPException
from ..core.db import engine, rows, one

router = APIRouter(tags=["Reporting units"])

@router.get("/reporting-units")
def list_reporting_units():
    with engine.connect() as connection:
        return rows(connection, """SELECT id, name, group_name AS "group", extension, phone,
            source_url, source_page, source_date, campus_location_id, contact_note
            FROM reporting_units WHERE active ORDER BY sort_order""")

def resolve_reporting_unit(connection, unit_id):
    if not unit_id:
        return None
    unit = one(connection, "SELECT id, name, phone FROM reporting_units WHERE id = :id AND active", id=unit_id)
    if not unit:
        raise HTTPException(422, "找不到指定的通報單位，請重新選擇")
    return unit
