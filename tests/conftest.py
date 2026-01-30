import pytest
import asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient, ASGITransport

from shared.db.base import Base
from app.main import app as fastapi_app
from app.db.session import get_session


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Database fixtures
@pytest.fixture
async def test_db_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest.fixture
async def async_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    async_session_maker = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session_maker() as session:
        yield session


@pytest.fixture
def mock_session():
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    session.rollback = AsyncMock()
    session.add = MagicMock()
    session.add_all = MagicMock()
    session.refresh = AsyncMock()
    return session


# RabbitMQ mock fixtures
@pytest.fixture
def mock_rabbitmq_exchange():
    exchange = AsyncMock()
    exchange.publish = AsyncMock()
    return exchange


@pytest.fixture
def mock_rabbitmq_channel(mock_rabbitmq_exchange):
    channel = AsyncMock()
    channel.declare_exchange = AsyncMock(return_value=mock_rabbitmq_exchange)
    channel.declare_queue = AsyncMock()
    return channel


@pytest.fixture
def mock_rabbitmq_connection(mock_rabbitmq_channel):
    connection = AsyncMock()
    connection.channel = AsyncMock(return_value=mock_rabbitmq_channel)
    connection.close = AsyncMock()
    return connection


@pytest.fixture
def mock_rabbitmq(mocker, mock_rabbitmq_connection, mock_rabbitmq_channel, mock_rabbitmq_exchange):
    mocker.patch('aio_pika.connect_robust', return_value=mock_rabbitmq_connection)
    
    return {
        'connection': mock_rabbitmq_connection,
        'channel': mock_rabbitmq_channel,
        'exchange': mock_rabbitmq_exchange
    }


@pytest.fixture
async def test_app(async_session):
    async def override_get_session():
        yield async_session
    
    fastapi_app.dependency_overrides[get_session] = override_get_session
    
    yield fastapi_app
    
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
async def async_client(test_app) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_order_producer(mocker):
    mock_producer = AsyncMock()
    mock_producer.connect = AsyncMock()
    mock_producer.publish_order_created = AsyncMock()
    mock_producer.close = AsyncMock()
    
    mocker.patch('app.api.orders.OrderProducer', return_value=mock_producer)
    
    return mock_producer


@pytest.fixture
def mock_rabbitmq_message():
    message = AsyncMock()
    message.body = b'{"event_id": "123", "payload": {"order_id": "550e8400-e29b-41d4-a716-446655440000"}}'
    message.process = MagicMock()
    message.process.return_value.__aenter__ = AsyncMock()
    message.process.return_value.__aexit__ = AsyncMock()
    return message

