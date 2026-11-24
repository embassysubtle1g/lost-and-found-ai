"""Case downlisting checks; optional PostgreSQL checks use rollback-only fixtures."""
import os
import unittest
from contextlib import contextmanager
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.api import radar


class CaseDeleteTests(unittest.TestCase):
    def test_missing_case_returns_404_without_update(self):
        with patch.object(radar.engine, "begin"), patch.object(radar, "one", return_value=None), patch.object(radar, "query") as update:
            response = TestClient(app).delete("/api/items/MISSING")
        self.assertEqual(response.status_code, 404)
        update.assert_not_called()

    def test_completed_case_preserves_return_history(self):
        with patch.object(radar.engine, "begin"), patch.object(radar, "one", return_value={"id": 1, "status": "RETURNED"}), patch.object(radar, "query") as update:
            response = TestClient(app).delete("/api/items/RETURNED-1")
        self.assertEqual(response.status_code, 409)
        update.assert_not_called()

    def test_repeated_delete_is_successful_without_mutation(self):
        with patch.object(radar.engine, "begin"), patch.object(radar, "one", return_value={"id": 1, "status": "WITHDRAWN"}), patch.object(radar, "query") as update:
            response = TestClient(app).delete("/api/items/WITHDRAWN-1")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")
        update.assert_not_called()


@unittest.skipUnless(os.getenv("RUN_CASE_DELETE_DB_TESTS") == "1", "Opt-in local PostgreSQL rollback checks")
class CaseDeleteDatabaseTests(unittest.TestCase):
    def test_lost_and_found_downlisting_and_retained_records(self):
        import uuid
        client = TestClient(app)
        # Never commit: fixtures and downlisting both roll back on exit.
        with radar.engine.connect() as connection:
            transaction = connection.begin()
            @contextmanager
            def shared_connection():
                yield connection
            try:
                with patch.object(radar.engine, "begin", shared_connection), patch.object(radar.engine, "connect", shared_connection):
                    token = uuid.uuid4().hex
                    org = radar.one(connection, "INSERT INTO organizations(name,address,phone) VALUES (:name,'test','test') RETURNING id", name="case-delete-" + token)
                    references = {}
                    ids = {}
                    for kind in ("LOST", "FOUND"):
                        reference = kind + "-DELETE-TEST-" + token
                        item = radar.one(connection, """INSERT INTO items(reference,organization_id,name,category,found_date,found_location,found_region,record_type,radar_data)
                            VALUES (:reference,:org,'delete test','test',CURRENT_DATE,'test','test',:kind,CAST(:data AS jsonb)) RETURNING id""",
                            reference=reference, org=org.id, kind=kind,
                            data='{"color":"red","tags":["test"]}')
                        ids[kind] = item.id
                        references[kind] = reference
                    radar.query(connection, "INSERT INTO dismissed_matches(lost_id,found_id) VALUES (:lost,:found)", lost=ids["LOST"],found=ids["FOUND"])
                    client.delete("/api/matches/dismissed")
                    def has_match():
                        return any(m["lost_item"]["item_id"] == references["LOST"] and m["found_item"]["item_id"] == references["FOUND"] for m in client.get("/api/matches").json())
                    self.assertTrue(has_match())
                    for kind in ("LOST", "FOUND"):
                        with self.subTest(record_type=kind):
                            image = radar.one(connection, """INSERT INTO item_images(item_id,object_key,media_type,size_bytes,is_cover)
                                VALUES (:item,:key,'image/png',1,true) RETURNING id""", item=ids[kind], key="test-delete/"+kind+token)
                            response = client.delete("/api/items/" + references[kind])
                            self.assertEqual(response.status_code, 204, response.text)
                            self.assertEqual(client.delete("/api/items/" + references[kind]).status_code, 204)
                            self.assertNotIn(references[kind], [i["item_id"] for i in client.get("/api/items").json()])
                            self.assertFalse(has_match())
                            self.assertEqual(client.get("/api/images/" + str(image.id)).status_code, 404)
                            self.assertEqual(client.get("/api/v1/public/images/" + str(image.id)).status_code, 404)
                            for action in ("confirm", "dismiss"):
                                self.assertEqual(client.post("/api/matches/" + action, json={"lost_id":references["LOST"],"found_id":references["FOUND"]}).status_code, 404)
                            self.assertEqual(client.delete("/api/matches/dismissed").status_code, 204)
                            self.assertFalse(has_match())
                            saved = radar.one(connection, "SELECT status FROM items WHERE id=:id", id=ids[kind])
                            self.assertEqual(saved.status, "WITHDRAWN")
                            self.assertIsNotNone(radar.one(connection, "SELECT id FROM item_images WHERE id=:id", id=image.id))
                            # Restore within this uncommitted fixture to test the other kind independently.
                            radar.query(connection, "UPDATE items SET status='AVAILABLE' WHERE id=:id", id=ids[kind])
                    radar.query(connection, "UPDATE items SET status='RETURNED', returned_at=now() WHERE id=:id", id=ids["LOST"])
                    self.assertEqual(client.delete("/api/items/"+references["LOST"]).status_code, 409)
                    self.assertEqual(client.delete("/api/items/DOES-NOT-EXIST-"+token).status_code, 404)
            finally:
                transaction.rollback()
