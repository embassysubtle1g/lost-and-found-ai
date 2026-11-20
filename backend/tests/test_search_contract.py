import io
import unittest
from datetime import date
from unittest.mock import patch

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.api import items
from app.services import media


class SearchContractTests(unittest.TestCase):
    def setUp(self):
        # No lifespan context is entered. External services are stubbed per test.
        self.client = TestClient(app)
        output = io.BytesIO()
        Image.new("RGB", (8, 8), "black").save(output, format="PNG")
        self.photo = output.getvalue()

    def test_photo_search_forwards_name_region_and_lost_date(self):
        with patch.object(items, "embedding", return_value="[1,0]"), \
             patch.object(items.engine, "connect"), \
             patch.object(items, "rows", return_value=[]) as result:
            response = self.client.post(
                "/api/v1/public/search",
                files={"file": ("wallet.png", self.photo, "image/png")},
                data={"keyword": "黑色錢包", "location": "屏東市", "lost_date": "2026-11-01"},
            )
        self.assertEqual(response.status_code, 200, response.text)
        parameters = result.call_args.kwargs
        self.assertEqual(parameters["keyword"], "黑色錢包")
        self.assertEqual(parameters["location"], "屏東市")
        self.assertEqual(parameters["lost_date"], date(2026, 11, 1))
        sql = result.call_args.args[1]
        self.assertIn("i.found_date >= CAST(:lost_date AS date)", sql)
        self.assertIn("MIN(embedding <=>", sql)
        self.assertIn("i.status = 'AVAILABLE'", sql)

    def test_photo_search_requires_photo(self):
        response = self.client.post("/api/v1/public/search", data={"keyword": "錢包"})
        self.assertEqual(response.status_code, 422)

    def test_bad_image_does_not_call_model(self):
        with patch.object(items, "embedding") as model:
            response = self.client.post(
                "/api/v1/public/search",
                files={"file": ("bad.png", b"not an image", "image/png")},
            )
        self.assertEqual(response.status_code, 400)
        model.assert_not_called()

    def test_ai_failure_returns_retryable_error(self):
        with patch.object(items, "embedding", side_effect=ValueError("wrong model")):
            response = self.client.post(
                "/api/v1/public/search",
                files={"file": ("wallet.png", self.photo, "image/png")},
            )
        self.assertEqual(response.status_code, 503)

    def test_staff_write_works_without_token(self):
        from app.core.organization import organization_context

        app.dependency_overrides[organization_context] = lambda: {"organization_id": 7}
        try:
            with patch.object(items.engine, "begin"), patch.object(
                items, "one", return_value={"id": 1, "name": "錢包"}
            ) as insert:
                response = self.client.post("/api/v1/staff/items", json={
                    "name": "錢包", "category": "證件錢包", "found_date": "2026-11-01",
                    "found_location": "一樓", "found_region": "屏東市",
                })
            self.assertEqual(response.status_code, 201, response.text)
            self.assertEqual(insert.call_args.kwargs["org"], 7)
        finally:
            app.dependency_overrides.clear()

    def test_return_without_account_records_time(self):
        from app.core.organization import organization_context

        app.dependency_overrides[organization_context] = lambda: {"organization_id": 7}
        try:
            with patch.object(items.engine, "begin"), \
                 patch.object(items, "owned", return_value={"status": "AVAILABLE"}), \
                 patch.object(items, "one", return_value={"id": 1, "status": "RETURNED"}) as update:
                response = self.client.post("/api/v1/staff/items/1/return")
            self.assertEqual(response.status_code, 200, response.text)
            self.assertIn("returned_at = now(), returned_by = NULL", update.call_args.args[1])
        finally:
            app.dependency_overrides.clear()

    def test_existing_item_payload_still_accepts_missing_region(self):
        from app.schemas.items import ItemData

        data = ItemData(name="錢包", category="證件錢包", found_date="2026-11-01",
                        found_location="屏東市")
        self.assertEqual(data.found_region, "")

    def test_dinov2_request_uses_file_and_validates_dimension(self):
        with patch.object(media.httpx, "post") as post:
            response = post.return_value
            response.json.return_value = {
                "status": "success", "model": media.MODEL, "model_version": media.VERSION,
                "embedding_dimension": 768, "embedding": [1.0] + [0.0] * 767,
            }
            media.embedding(self.photo, "image/png")
            self.assertIn("file", post.call_args.kwargs["files"])
            self.assertTrue(post.call_args.args[0].endswith("/api/v1/images/embedding"))
            response.json.return_value["embedding_dimension"] = 384
            with self.assertRaises(ValueError):
                media.embedding(self.photo, "image/png")


if __name__ == "__main__":
    unittest.main()
