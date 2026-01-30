import pytest
import uuid
from decimal import Decimal
from unittest.mock import MagicMock

from consumer.services.order_processor import OrderProcessor
from shared.db.models import Order


@pytest.mark.asyncio
async def test_process_existing_order(mock_session):
    processor = OrderProcessor()
    order_id = uuid.uuid4()
    
    mock_order = Order(
        id=order_id,
        customer_id=uuid.uuid4(),
        status="NEW",
        total_price=Decimal("100.00"),
    )
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_order
    mock_session.execute.return_value = mock_result
    
    await processor.process(mock_session, order_id)
    
    assert mock_order.status == "PROCESSED"
    
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_process_order_not_found(mock_session):
    processor = OrderProcessor()
    order_id = uuid.uuid4()
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    
    with pytest.raises(ValueError) as exc_info:
        await processor.process(mock_session, order_id)
    
    assert f"Order {order_id} not found" in str(exc_info.value)
    
    mock_session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_process_changes_status_to_processed(mock_session):
    processor = OrderProcessor()
    order_id = uuid.uuid4()
    
    mock_order = Order(
        id=order_id,
        customer_id=uuid.uuid4(),
        status="NEW",
        total_price=Decimal("50.00"),
    )
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_order
    mock_session.execute.return_value = mock_result
    
    await processor.process(mock_session, order_id)
    
    assert mock_order.status == "PROCESSED"


@pytest.mark.asyncio
async def test_process_commits_to_database(mock_session):
    processor = OrderProcessor()
    order_id = uuid.uuid4()
    
    mock_order = Order(
        id=order_id,
        customer_id=uuid.uuid4(),
        status="NEW",
        total_price=Decimal("75.00"),
    )
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_order
    mock_session.execute.return_value = mock_result
    
    await processor.process(mock_session, order_id)
    
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_process_executes_select_query(mock_session):
    processor = OrderProcessor()
    order_id = uuid.uuid4()
    
    mock_order = Order(
        id=order_id,
        customer_id=uuid.uuid4(),
        status="NEW",
        total_price=Decimal("100.00"),
    )
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_order
    mock_session.execute.return_value = mock_result
    
    await processor.process(mock_session, order_id)
    
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_process_multiple_orders(mock_session):
    processor = OrderProcessor()
    
    order_id_1 = uuid.uuid4()
    order_id_2 = uuid.uuid4()
    
    mock_order_1 = Order(
        id=order_id_1,
        customer_id=uuid.uuid4(),
        status="NEW",
        total_price=Decimal("100.00"),
    )
    
    mock_order_2 = Order(
        id=order_id_2,
        customer_id=uuid.uuid4(),
        status="NEW",
        total_price=Decimal("200.00"),
    )
    
    mock_result_1 = MagicMock()
    mock_result_1.scalar_one_or_none.return_value = mock_order_1
    
    mock_result_2 = MagicMock()
    mock_result_2.scalar_one_or_none.return_value = mock_order_2
    
    mock_session.execute.side_effect = [mock_result_1, mock_result_2]
    
    await processor.process(mock_session, order_id_1)
    await processor.process(mock_session, order_id_2)
    
    assert mock_order_1.status == "PROCESSED"
    assert mock_order_2.status == "PROCESSED"
    assert mock_session.commit.call_count == 2

