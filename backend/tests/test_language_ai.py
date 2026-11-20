import unittest
from unittest.mock import patch

import httpx
from fastapi import HTTPException
from app.services.language_ai import classify_photo


class LanguageAiTests(unittest.TestCase):
    def result(self):
        return {
            "detected_item": "黑色短夾", "suggested_category": "皮夾",
            "description": "黑色拉鍊式短夾",
            "attributes": {"color": "黑色", "material": None, "brand": None,
                           "distinctive_features": ["拉鍊", "卡片夾層"]},
            "confidence": 0.92, "needs_review": True,
        }

    def test_contract_mapping_and_multipart(self):
        with patch("app.services.language_ai.httpx.post") as post:
            post.return_value.json.return_value = self.result()
            result = classify_photo(b"photo", "image/png")
        self.assertTrue(post.call_args.args[0].endswith("/api/v1/images/classify"))
        self.assertEqual(post.call_args.kwargs["files"]["file"][1], b"photo")
        self.assertEqual(result["category"], "皮夾")
        self.assertEqual(result["description"], "黑色拉鍊式短夾")
        self.assertTrue(result["needs_review"])
        self.assertEqual(result["tags"], ["拉鍊", "卡片夾層"])

    def test_null_color_is_editable_empty_string(self):
        payload = self.result()
        payload["attributes"]["color"] = None
        with patch("app.services.language_ai.httpx.post") as post:
            post.return_value.json.return_value = payload
            self.assertEqual(classify_photo(b"photo", "image/png")["color"], "")

    def test_malformed_response_returns_502(self):
        with patch("app.services.language_ai.httpx.post") as post:
            post.return_value.json.return_value = {"detected_item": "錢包"}
            with self.assertRaises(HTTPException) as caught:
                classify_photo(b"photo", "image/png")
        self.assertEqual(caught.exception.status_code, 502)

    def test_timeout_is_recoverable(self):
        with patch("app.services.language_ai.httpx.post", side_effect=httpx.ReadTimeout("slow")):
            with self.assertRaises(HTTPException) as caught:
                classify_photo(b"photo", "image/png")
        self.assertEqual(caught.exception.status_code, 504)

    def test_service_failure_is_recoverable(self):
        with patch("app.services.language_ai.httpx.post", side_effect=httpx.ConnectError("offline")):
            with self.assertRaises(HTTPException) as caught:
                classify_photo(b"photo", "image/png")
        self.assertEqual(caught.exception.status_code, 503)

    def test_frontend_recognition_endpoint_calls_language_service(self):
        import base64
        import io
        from PIL import Image
        from fastapi.testclient import TestClient
        from app.main import app

        image = io.BytesIO()
        Image.new("RGB", (4, 4), "black").save(image, format="PNG")
        data_url = "data:image/png;base64," + base64.b64encode(image.getvalue()).decode()
        with patch("app.api.radar.classify_photo", return_value={"title": "黑色短夾"}) as classify:
            response = TestClient(app).post("/api/ai-recognize", json={"image": data_url})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["title"], "黑色短夾")
        self.assertEqual(classify.call_args.args[1], "image/png")
