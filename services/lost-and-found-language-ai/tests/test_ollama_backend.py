import base64
import unittest
from unittest.mock import patch
import httpx
from PIL import Image
from app.models import ollama_vision

class LocalVisionTests(unittest.TestCase):
    def test_valid_image_and_completed_response(self):
        response = httpx.Response(200, json={"done": True, "message": {"content": '{"detected_item":"red cup"}'}}, request=httpx.Request("POST", "http://local/api/chat"))
        with patch("app.models.ollama_vision.httpx.post", return_value=response) as post:
            result = ollama_vision.generate(Image.new("RGB", (2000, 1000), "red"), "describe")
        self.assertIn("red cup", result)
        payload = post.call_args.kwargs["json"]
        self.assertEqual(payload["options"]["num_ctx"], 4096)
        self.assertTrue(base64.b64decode(payload["messages"][0]["images"][0]).startswith(b"\xff\xd8"))

    def test_busy_request_does_not_queue_second_model(self):
        ollama_vision._generation_lock.acquire()
        try:
            with self.assertRaisesRegex(RuntimeError, "辨識進行中"):
                ollama_vision.generate(Image.new("RGB", (5, 5)), "describe")
        finally:
            ollama_vision._generation_lock.release()

    def test_connection_error_releases_generation_lock(self):
        with patch("app.models.ollama_vision.httpx.post", side_effect=httpx.ConnectError("offline")):
            with self.assertRaises(RuntimeError):
                ollama_vision.generate(Image.new("RGB", (5, 5)), "describe")
        self.assertFalse(ollama_vision._generation_lock.locked())

    def test_truncated_output_is_rejected(self):
        response = httpx.Response(200, json={"done": True, "done_reason": "length", "message": {"content": "{}"}}, request=httpx.Request("POST", "http://local/api/chat"))
        with patch("app.models.ollama_vision.httpx.post", return_value=response):
            with self.assertRaisesRegex(RuntimeError, "輸出未完成"):
                ollama_vision.generate(Image.new("RGB", (5, 5)), "describe")
