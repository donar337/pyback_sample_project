from fastapi import FastAPI

from app.api.orders import router as orders_router
from app.metrics.prometheus import setup_metrics

app = FastAPI(title="Order Processing Service")

setup_metrics(app)

app.include_router(orders_router, prefix="/orders", tags=["orders"])


@app.get("/health")
async def health():
    return {"status": "ok"}
