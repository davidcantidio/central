# Importe a instância app do seu módulo FastAPI
from fast_api_app.main import app
from httpx import AsyncClient
from httpx._transports.asgi import ASGITransport
import pytest

@pytest.mark.asyncio
async def test_hello():
    async with AsyncClient(transport=ASGITransport(app=app)) as client:
        response = await client.get("http://test/")
        assert response.status_code == 200
        assert response.text == '"Hello, FastAPI!"'
