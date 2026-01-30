import pytest
from fastapi import FastAPI

from app.metrics.prometheus import setup_metrics, REQUEST_COUNT, REQUEST_LATENCY


def test_setup_metrics_mounts_endpoint():
    app = FastAPI()
    
    setup_metrics(app)
    
    routes = [route.path for route in app.routes]
    assert "/metrics" in routes


@pytest.mark.asyncio
async def test_metrics_middleware_increments_counter():
    app = FastAPI()
    setup_metrics(app)
    
    @app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}
    
    initial_value = REQUEST_COUNT.labels(method="GET", path="/test")._value._value
    
    from httpx import AsyncClient, ASGITransport
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/test")
    
    assert response.status_code == 200
    
    final_value = REQUEST_COUNT.labels(method="GET", path="/test")._value._value
    assert final_value > initial_value


@pytest.mark.asyncio
async def test_metrics_middleware_records_latency():
    app = FastAPI()
    setup_metrics(app)
    
    @app.get("/slow")
    async def slow_endpoint():
        import asyncio
        await asyncio.sleep(0.01)
        return {"status": "ok"}
    
    initial_count = REQUEST_LATENCY.labels(method="GET", path="/slow")._sum._value
    
    from httpx import AsyncClient, ASGITransport
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/slow")
    
    assert response.status_code == 200
    
    final_count = REQUEST_LATENCY.labels(method="GET", path="/slow")._sum._value
    assert final_count > initial_count


@pytest.mark.asyncio
async def test_metrics_middleware_handles_different_paths():
    app = FastAPI()
    setup_metrics(app)
    
    @app.get("/path1")
    async def path1():
        return {"path": "1"}
    
    @app.get("/path2")
    async def path2():
        return {"path": "2"}
    
    from httpx import AsyncClient, ASGITransport
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.get("/path1")
        await client.get("/path2")
    
    path1_count = REQUEST_COUNT.labels(method="GET", path="/path1")._value._value
    path2_count = REQUEST_COUNT.labels(method="GET", path="/path2")._value._value
    
    assert path1_count >= 1
    assert path2_count >= 1


@pytest.mark.asyncio
async def test_metrics_middleware_handles_different_methods():
    app = FastAPI()
    setup_metrics(app)
    
    @app.get("/resource")
    async def get_resource():
        return {"method": "GET"}
    
    @app.post("/resource")
    async def post_resource():
        return {"method": "POST"}
    
    from httpx import AsyncClient, ASGITransport
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.get("/resource")
        await client.post("/resource")
    
    get_count = REQUEST_COUNT.labels(method="GET", path="/resource")._value._value
    post_count = REQUEST_COUNT.labels(method="POST", path="/resource")._value._value
    
    assert get_count >= 1
    assert post_count >= 1


@pytest.mark.asyncio
async def test_metrics_middleware_passes_response_through():
    app = FastAPI()
    setup_metrics(app)
    
    @app.get("/data")
    async def get_data():
        return {"key": "value", "number": 42}
    
    from httpx import AsyncClient, ASGITransport
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/data")
    
    assert response.status_code == 200
    data = response.json()
    assert data["key"] == "value"
    assert data["number"] == 42


def test_request_count_metric_exists():
    assert REQUEST_COUNT is not None
    assert REQUEST_COUNT._name in ["http_requests_total", "http_requests"]


def test_request_latency_metric_exists():
    assert REQUEST_LATENCY is not None
    assert REQUEST_LATENCY._name == "http_request_duration_seconds"

