import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_health(async_client):
    resp = await async_client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_api_hello(async_client):
    resp = await async_client.get("/api/hello")
    assert resp.status_code == 200
    data = resp.json()
    assert data["msg"] == "hello world"


@pytest.mark.asyncio
async def test_api_add(async_client):
    resp = await async_client.post("/api/add", params={"a": 12, "b": 34})
    assert resp.status_code == 200
    assert resp.json()["sum"] == 46


@pytest.mark.asyncio
async def test_api_webhook_fail(async_client):
    resp = await async_client.get("/api/webhook_fail")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_api_fake_500(async_client):
    resp = await async_client.get("/api/fake_500")
    assert resp.status_code == 500


@pytest.mark.asyncio
async def test_metrics_endpoint(async_client):
    resp = await async_client.get("/metrics")
    assert resp.status_code == 200
    assert "webhook_sign_verify_failed_total" in resp.text
