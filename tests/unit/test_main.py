import pytest
from fastapi.testclient import TestClient

from app.main import app


def test_app_instance():
    assert app.title == "Order Processing Service"


def test_app_has_orders_router():
    routes = [route.path for route in app.routes]
    assert "/orders/" in routes or any("/orders" in route for route in routes)


def test_app_has_health_endpoint():
    routes = [route.path for route in app.routes]
    assert "/health" in routes


def test_app_has_metrics_endpoint():
    routes = [route.path for route in app.routes]
    assert "/metrics" in routes


def test_health_endpoint_sync():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

