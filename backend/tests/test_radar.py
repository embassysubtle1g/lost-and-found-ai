import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.api import radar


class RadarTests(unittest.TestCase):
    def test_no_auth_on_radar_routes(self):
        paths = app.openapi()["paths"]
        for path in ("/api/items", "/api/matches", "/api/ai-recognize", "/api/matches/confirm"):
            self.assertIn(path, paths)
            for operation in paths[path].values():
                self.assertFalse(operation.get("security"))

    def test_no_fabricated_recognition_when_model_unavailable(self):
        response = TestClient(app).post("/api/ai-recognize", json={"image": "invalid"})
        self.assertEqual(response.status_code, 400)

    def test_pair_confirmation_is_atomic_and_requires_open_records(self):
        with patch.object(radar.engine, "begin"), patch.object(
            radar, "pair_records",
            return_value=({"id": 1, "status": "AVAILABLE"}, {"id": 2, "status": "RETURNED"})
        ), patch.object(radar, "query") as update:
            response = TestClient(app).post("/api/matches/confirm", json={"lost_id":"LOST-1","found_id":"FOUND-2"})
        self.assertEqual(response.status_code, 409)
        update.assert_not_called()

    def test_client_does_not_choose_report_id_or_state(self):
        data = radar.Report(record_type="LOST", title="錢包", category="證件錢包",
                            location="圖書館", datetime="2026-11-18T12:00",
                            user_name="測試人", user_contact="測試聯絡方式",
                            item_id="FORGED", status="MATCHED")
        self.assertNotIn("item_id", data.model_dump())
        self.assertNotIn("status", data.model_dump())
