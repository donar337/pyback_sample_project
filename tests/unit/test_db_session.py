import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import engine, AsyncSessionLocal, get_session


def test_engine_exists():
    assert engine is not None


def test_async_session_local_exists():
    assert AsyncSessionLocal is not None


@pytest.mark.asyncio
async def test_get_session_yields_session():
    gen = get_session()
    session = await gen.__anext__()
    
    assert isinstance(session, AsyncSession)
    
    try:
        await gen.__anext__()
    except StopAsyncIteration:
        pass


def test_engine_url_contains_postgresql():
    url_str = str(engine.url)
    assert "postgresql" in url_str or "sqlite" in url_str


def test_async_session_local_class():
    assert hasattr(AsyncSessionLocal, 'class_') or hasattr(AsyncSessionLocal, 'kw')


def test_consumer_db_session():
    from consumer.db.session import engine as consumer_engine
    from consumer.db.session import AsyncSessionLocal as ConsumerSessionLocal
    
    assert consumer_engine is not None
    assert ConsumerSessionLocal is not None

