from functools import wraps
from app.database.session import get_session


def db_session_middleware(func):
    """Decorator to inject an async db session into handler calls."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        async with get_session() as session:
            kwargs["db"] = session
            return await func(*args, **kwargs)
    return wrapper
