import unittest
from pathlib import Path

from app.main import DEMO, app


class ApiLayoutTests(unittest.TestCase):
    def test_main_keeps_public_and_staff_api_registered(self):
        paths = app.openapi()["paths"]
        expected = {
            "/health": "get",
            "/api/v1/public/items": "get",
            "/api/v1/public/search": "post",
            "/api/v1/auth/login": "post",
            "/api/v1/staff/items": "post",
            "/api/v1/staff/items/{item_id}/images": "post",
            "/api/v1/staff/items/{item_id}/return": "post",
        }
        for path, method in expected.items():
            with self.subTest(path=path, method=method):
                self.assertIn(method, paths.get(path, {}))

    def test_demo_assets_resolve_from_backend(self):
        backend = Path(__file__).resolve().parents[1]
        self.assertEqual(DEMO, backend / "app" / "api" / "demo")
        self.assertTrue((DEMO / "index.html").is_file())
