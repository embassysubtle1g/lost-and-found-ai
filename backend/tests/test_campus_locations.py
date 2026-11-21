import unittest
from unittest.mock import patch
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app.main import app
from app.api import locations

class CampusLocationsTests(unittest.TestCase):
    def test_location_endpoint_has_no_login_requirement(self):
        self.assertIn('/api/locations', app.openapi()['paths'])
        with patch.object(locations.engine, 'connect'), patch.object(locations, 'rows', return_value=[{'id':'NPUST-009','name':'圖書與會展館'}]):
            response = TestClient(app).get('/api/locations')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]['id'], 'NPUST-009')

    def test_alias_can_use_canonical_location_id(self):
        record={'id':'NPUST-009','name':'圖書與會展館','aliases':['圖書館']}
        with patch.object(locations, 'one', return_value=record):
            self.assertEqual(locations.resolve_location(None,'NPUST-009','圖書館')['name'],'圖書與會展館')

    def test_inconsistent_id_and_name_is_rejected(self):
        with patch.object(locations, 'one', return_value={'id':'NPUST-009','name':'圖書與會展館','aliases':['圖書館']}):
            with self.assertRaises(HTTPException) as result:
                locations.resolve_location(None,'NPUST-009','校門口')
        self.assertEqual(result.exception.status_code,422)

    def test_missing_location_id_is_rejected(self):
        with patch.object(locations, 'one', return_value=None):
            with self.assertRaises(HTTPException):locations.resolve_location(None,'NPUST-999','圖書館')

    def test_legacy_custom_location_stays_usable(self):
        with patch.object(locations, 'one', return_value=None):
            self.assertIsNone(locations.resolve_location(None,None,'其他自訂地點'))
