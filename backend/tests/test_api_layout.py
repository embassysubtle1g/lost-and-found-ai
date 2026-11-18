import unittest
from pathlib import Path

from app.main import FRONTEND, app, frontend


class ApiLayoutTests(unittest.TestCase):
    def test_main_keeps_public_and_management_api_registered(self):
        paths = app.openapi()["paths"]
        expected = {
            "/health": "get",
            "/api/v1/public/items": "get",
            "/api/v1/public/search": "post",
            "/api/v1/staff/organizations": "post",
            "/api/v1/staff/items": "post",
            "/api/v1/staff/items/{item_id}/images": "post",
            "/api/v1/staff/items/{item_id}/return": "post",
        }
        for path, method in expected.items():
            with self.subTest(path=path, method=method):
                operation = paths.get(path, {}).get(method, {})
                self.assertTrue(operation)
                self.assertFalse(operation.get("security"))
        self.assertFalse(any("/auth/" in path for path in paths))

    def test_only_react_frontend_is_served(self):
        backend = Path(__file__).resolve().parents[1]
        self.assertEqual(FRONTEND, backend.parent / "frontend" / "dist")
        response = frontend()
        if (FRONTEND / "index.html").is_file():
            self.assertEqual(response.status_code, 200)
            self.assertEqual(Path(response.path), FRONTEND / "index.html")
        else:
            self.assertEqual(response.status_code, 503)
            self.assertIn("請先建置新版前端", response.body.decode())
