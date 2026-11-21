"""Campus map catalogue and optional report location relationship."""
import json
from alembic import op
revision = "0005"
down_revision = "0004"

LOCATIONS = json.loads(r'''[{"id": "NPUST-001", "name": "校門口", "zone": "西側入口與服務", "x": 418.8, "y": 627.0, "labelX": 418.8, "labelY": 594.0, "aliases": []}, {"id": "NPUST-002", "name": "獸醫院", "zone": "西側入口與服務", "x": 461.8, "y": 556.0, "labelX": 461.8, "labelY": 523.0, "aliases": []}, {"id": "NPUST-003", "name": "工作犬訓練中心", "zone": "西側入口與服務", "x": 378.8, "y": 348.0, "labelX": 378.8, "labelY": 315.0, "aliases": []}, {"id": "NPUST-004", "name": "蝴蝶湖", "zone": "西側入口與服務", "x": 418.8, "y": 387.0, "labelX": 418.8, "labelY": 354.0, "aliases": []}, {"id": "NPUST-005", "name": "生物科技系", "zone": "中央教學與行政", "x": 465.8, "y": 480.0, "labelX": 465.8, "labelY": 447.0, "aliases": []}, {"id": "NPUST-006", "name": "情人坡", "zone": "中央教學與行政", "x": 632.8, "y": 431.0, "labelX": 632.8, "labelY": 398.0, "aliases": []}, {"id": "NPUST-007", "name": "國際學院", "zone": "中央教學與行政", "x": 635.0, "y": 350.0, "labelX": 635.0, "labelY": 317.0, "aliases": []}, {"id": "NPUST-008", "name": "行政中心", "zone": "中央教學與行政", "x": 744.2, "y": 348.0, "labelX": 744.2, "labelY": 315.0, "aliases": []}, {"id": "NPUST-009", "name": "圖書與會展館", "zone": "中央教學與行政", "x": 726.0, "y": 296.0, "labelX": 726.0, "labelY": 243.0, "aliases": ["圖書館"]}, {"id": "NPUST-010", "name": "綜合體育館", "zone": "中央教學與行政", "x": 644.5, "y": 286.0, "labelX": 644.5, "labelY": 253.0, "aliases": []}, {"id": "NPUST-011", "name": "工學院", "zone": "北側教學研究", "x": 527.8, "y": 280.0, "labelX": 527.8, "labelY": 247.0, "aliases": []}, {"id": "NPUST-012", "name": "食品科學系", "zone": "北側教學研究", "x": 594.2, "y": 236.0, "labelX": 594.2, "labelY": 203.0, "aliases": []}, {"id": "NPUST-013", "name": "農學院", "zone": "北側教學研究", "x": 619.0, "y": 171.0, "labelX": 619.0, "labelY": 138.0, "aliases": []}, {"id": "NPUST-014", "name": "管理學院", "zone": "北側教學研究", "x": 688.2, "y": 200.0, "labelX": 688.2, "labelY": 167.0, "aliases": []}, {"id": "NPUST-015", "name": "木材科學與設計系", "zone": "北側教學研究", "x": 733.8, "y": 248.0, "labelX": 733.8, "labelY": 195.0, "aliases": ["木材設計系"]}, {"id": "NPUST-016", "name": "第一餐廳", "zone": "東側生活與體育", "x": 796.8, "y": 116.0, "labelX": 796.8, "labelY": 83.0, "aliases": ["第一學生餐廳"]}, {"id": "NPUST-017", "name": "游泳池", "zone": "東側生活與體育", "x": 757.2, "y": 203.0, "labelX": 757.2, "labelY": 170.0, "aliases": []}, {"id": "NPUST-018", "name": "棒壘球場", "zone": "東側生活與體育", "x": 816.8, "y": 175.0, "labelX": 816.8, "labelY": 142.0, "aliases": []}, {"id": "NPUST-019", "name": "運動場", "zone": "東側生活與體育", "x": 872.0, "y": 209.0, "labelX": 872.0, "labelY": 176.0, "aliases": []}, {"id": "NPUST-020", "name": "第二餐廳", "zone": "東側生活與體育", "x": 952.8, "y": 152.0, "labelX": 952.8, "labelY": 119.0, "aliases": []}, {"id": "NPUST-021", "name": "人文暨社會科學院", "zone": "東側生活與體育", "x": 927.5, "y": 100.0, "labelX": 927.5, "labelY": 67.0, "aliases": []}, {"id": "NPUST-022", "name": "孟祥體育館", "zone": "東側生活與體育", "x": 906.2, "y": 241.0, "labelX": 906.2, "labelY": 208.0, "aliases": []}, {"id": "NPUST-023", "name": "水生生物科學系", "zone": "南側教學與水產", "x": 935.0, "y": 298.0, "labelX": 935.0, "labelY": 265.0, "aliases": []}, {"id": "NPUST-024", "name": "景觀暨遊憩管理系", "zone": "南側教學與水產", "x": 901.5, "y": 342.0, "labelX": 901.5, "labelY": 309.0, "aliases": []}, {"id": "NPUST-025", "name": "水產養殖系實習場", "zone": "南側教學與水產", "x": 773.0, "y": 485.0, "labelX": 773.0, "labelY": 452.0, "aliases": []}, {"id": "NPUST-026", "name": "水產養殖研究中心", "zone": "南側教學與水產", "x": 845.2, "y": 432.0, "labelX": 845.2, "labelY": 399.0, "aliases": []}, {"id": "NPUST-027", "name": "水族醫學中心", "zone": "南側教學與水產", "x": 913.2, "y": 400.0, "labelX": 913.2, "labelY": 367.0, "aliases": []}]''')

def quoted(value):
    return "'" + str(value).replace("'", "''") + "'"

def upgrade():
    op.execute("""CREATE TABLE campus_locations (
        id text PRIMARY KEY,
        name text NOT NULL UNIQUE,
        zone text NOT NULL,
        map_x double precision NOT NULL,
        map_y double precision NOT NULL,
        label_x double precision NOT NULL,
        label_y double precision NOT NULL,
        sort_order integer NOT NULL,
        aliases jsonb NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(aliases) = 'array')
    )""")
    for index, loc in enumerate(LOCATIONS, 1):
        values = [quoted(loc['id']), quoted(loc['name']), quoted(loc['zone']),
                  str(loc['x']), str(loc['y']), str(loc['labelX']), str(loc['labelY']),
                  str(index), quoted(json.dumps(loc['aliases'], ensure_ascii=False)) + '::jsonb']
        op.execute('INSERT INTO campus_locations VALUES (' + ','.join(values) + ')')
    op.execute("ALTER TABLE items ADD COLUMN campus_location_id text REFERENCES campus_locations(id)")
    op.execute("CREATE INDEX items_campus_location_idx ON items(campus_location_id)")
    op.execute("""UPDATE items i SET campus_location_id = c.id
        FROM campus_locations c
        WHERE COALESCE(NULLIF(i.found_region, ''), i.found_location) = c.name
           OR c.aliases ? COALESCE(NULLIF(i.found_region, ''), i.found_location)""")

def downgrade():
    op.execute("ALTER TABLE items DROP COLUMN campus_location_id")
    op.execute("DROP TABLE campus_locations")
