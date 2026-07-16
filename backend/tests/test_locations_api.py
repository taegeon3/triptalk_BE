import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.main import app

client = TestClient(app)


def test_locations_list_returns_data():
    response = client.get('/locations/')
    assert response.status_code == 200
    payload = response.json()
    assert 'locations' in payload
    assert isinstance(payload['locations'], list)


def test_locations_detail_returns_404_for_missing_id():
    response = client.get('/locations/content/does-not-exist')
    assert response.status_code == 404


def test_locations_filter_by_content_type_id():
    response = client.get('/locations/', params={'contentTypeId': 12})
    assert response.status_code == 200
    payload = response.json()
    items = payload['locations']
    assert all(item['contentId'] for item in items)


def test_locations_filter_by_numeric_area_and_sigungu_codes():
    response = client.get('/locations/', params={'areaCode': 5, 'sigunguCode': 1})
    assert response.status_code == 200
    payload = response.json()
    items = payload['locations']
    assert items
    assert all(item['title'] for item in items)
