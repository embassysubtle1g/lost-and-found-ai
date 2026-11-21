import unittest
from unittest.mock import patch
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app.main import app
from app.api import reporting_units, radar

class ReportingUnitsTests(unittest.TestCase):
    def test_directory_is_available_without_login(self):
        with patch.object(reporting_units.engine,'connect'), patch.object(reporting_units,'rows',return_value=[{'id':'UNIT-006','name':'圖書與會展館','phone':'08-7703202 分機 7269'}]):
            response=TestClient(app).get('/api/reporting-units')
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()[0]['phone'],'08-7703202 分機 7269')

    def test_unknown_unit_is_rejected(self):
        with patch.object(reporting_units,'one',return_value=None):
            with self.assertRaises(HTTPException) as error:reporting_units.resolve_reporting_unit(None,'UNIT-MISSING')
        self.assertEqual(error.exception.status_code,422)

    def test_legacy_request_does_not_require_directory_selection(self):
        with patch.object(reporting_units,'one') as query:
            self.assertIsNone(reporting_units.resolve_reporting_unit(None,None))
        query.assert_not_called()

    def test_invalid_unit_is_rejected_before_photo_upload(self):
        data={'record_type':'FOUND','title':'test','category':'test','location':'test','datetime':'2026-11-21T12:00','user_name':'test','user_contact':'test','reporting_unit_id':'UNIT-MISSING','image_url':'invalid photo'}
        with patch.object(radar.engine,'connect'),patch.object(radar,'resolve_location',return_value=None),patch.object(radar,'resolve_reporting_unit',side_effect=HTTPException(422,'unknown unit')),patch.object(radar,'read_data_image') as photo:
            response=TestClient(app).post('/api/items',json=data)
        self.assertEqual(response.status_code,422)
        photo.assert_not_called()
