import pytest
from app.middleware.anti_spam import check_rate_limit, set_maintenance_mode, is_maintenance_mode


@pytest.mark.asyncio
async def test_rate_limiter():
    user_id = 77777

    # First call: Not limited
    is_limited_1, _ = await check_rate_limit(user_id, "test_action", limit_seconds=1.0)
    assert is_limited_1 is False

    # Second immediate call: Rate limited
    is_limited_2, wait_time = await check_rate_limit(user_id, "test_action", limit_seconds=1.0)
    assert is_limited_2 is True
    assert wait_time > 0.0


def test_maintenance_flag():
    set_maintenance_mode(True)
    assert is_maintenance_mode() is True
    set_maintenance_mode(False)
    assert is_maintenance_mode() is False
