from types import SimpleNamespace
from api.dashboard import require_api_token
from config import settings
import pytest


@pytest.mark.parametrize("path,token,header,allowed", [
    ("/health", "", "", True),
    ("/inventory", "", "", False),
    ("/inventory", "test-key", "Bearer wrong", False),
    ("/inventory", "test-key", "Bearer test-key", True),
])
async def test_api_token_gate(monkeypatch, path, token, header, allowed):
    monkeypatch.setattr(settings, "api_token", token)
    request = SimpleNamespace(url=SimpleNamespace(path=path), headers={"Authorization": header})
    async def next_handler(request):
        return SimpleNamespace(status_code=200)
    response = await require_api_token(request, next_handler)
    assert response.status_code == (200 if allowed else 401)
