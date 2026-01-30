import uuid
from decimal import Decimal
from datetime import datetime
import factory
from app.api.schemas import OrderCreate, OrderItemCreate


class OrderItemCreateSchemaFactory(Factory):
    class Meta:
        model = OrderItemCreate
    
    product_id = factory.LazyFunction(uuid.uuid4)
    quantity = factory.Faker('pyint', min_value=1, max_value=10)
    price = factory.LazyFunction(lambda: Decimal(str(factory.Faker('pyfloat', min_value=1.0, max_value=1000.0, right_digits=2).generate({}))))


class OrderCreateSchemaFactory(Factory):
    class Meta:
        model = OrderCreate
    
    customer_id = factory.LazyFunction(uuid.uuid4)
    items = factory.LazyAttribute(lambda obj: [OrderItemCreateSchemaFactory() for _ in range(2)])


class OrderItemDataFactory(Factory):
    class Meta:
        model = dict
    
    product_id = factory.LazyFunction(uuid.uuid4)
    quantity = factory.Faker('pyint', min_value=1, max_value=10)
    price = factory.LazyFunction(lambda: Decimal(str(factory.Faker('pyfloat', min_value=1.0, max_value=1000.0, right_digits=2).generate({}))))


class OrderDataFactory(Factory):
    class Meta:
        model = dict
    
    id = factory.LazyFunction(uuid.uuid4)
    customer_id = factory.LazyFunction(uuid.uuid4)
    status = "NEW"
    total_price = factory.LazyFunction(lambda: Decimal(str(factory.Faker('pyfloat', min_value=10.0, max_value=5000.0, right_digits=2).generate({}))))
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)

