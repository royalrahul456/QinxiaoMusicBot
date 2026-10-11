import pytest
from app.permissions.checker import Role, is_owner, check_min_role
from app.config.settings import settings


@pytest.mark.asyncio
async def test_owner_permission(monkeypatch):
    monkeypatch.setattr(settings, "OWNER_ID", 123456789)
    assert await is_owner(123456789) is True
    assert await is_owner(999999999) is False
    assert await is_owner(0) is False


@pytest.mark.asyncio
async def test_role_hierarchy():
    assert Role.OWNER > Role.SUDO
    assert Role.SUDO > Role.ADMIN
    assert Role.ADMIN > Role.USER
