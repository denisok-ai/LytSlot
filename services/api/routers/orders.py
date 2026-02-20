"""
@file: orders.py
@description: Orders - create, list, get by id, update status (tenant-scoped).
@dependencies: fastapi, db.models, shared.schemas
@created: 2025-02-19
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.models import Order, OrderStatus
from services.api.auth import get_current_user_id
from services.api.config import settings
from services.api.deps import get_db_with_required_tenant
from services.api.logging_config import get_logger
from shared.schemas import OrderCreate, OrderUpdate

logger = get_logger(__name__)

router = APIRouter(prefix="/orders", tags=["orders"])


class OrderResponse(BaseModel):
    id: UUID
    advertiser_id: int
    channel_id: UUID
    slot_id: UUID
    content: dict
    erid: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=list[OrderResponse], summary="Список заказов")
def list_orders(db: Session = Depends(get_db_with_required_tenant)):
    """Все заказы текущего tenant."""
    orders = db.query(Order).all()
    return [OrderResponse.model_validate(o) for o in orders]


@router.get("/{order_id}", response_model=OrderResponse, summary="Заказ по ID")
def get_order(order_id: UUID, db: Session = Depends(get_db_with_required_tenant)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return OrderResponse.model_validate(order)


@router.post("", response_model=OrderResponse, status_code=201, summary="Создать заказ")
def create_order(
    request: Request,
    body: OrderCreate,
    db: Session = Depends(get_db_with_required_tenant),
    user_id: int = Depends(get_current_user_id),
):
    order = Order(
        advertiser_id=user_id,
        channel_id=body.channel_id,
        slot_id=body.slot_id,
        content=body.content,
        erid=body.erid,
        status=OrderStatus.DRAFT,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    request_id = getattr(request.state, "request_id", None)
    if settings.celery_broker_url:
        try:
            from services.worker.tasks import notify_new_order, publish_order

            publish_order.delay(str(order.id), request_id=request_id)
            notify_new_order.delay(str(order.id), request_id=request_id)
        except Exception:
            logger.warning("Failed to enqueue tasks", exc_info=True)
    else:
        logger.info(
            "Worker disabled (CELERY_BROKER_URL not set); skipping publish_order, notify_new_order"
        )
    return OrderResponse.model_validate(order)


@router.patch("/{order_id}", response_model=OrderResponse, summary="Обновить статус заказа")
def update_order(
    request: Request,
    order_id: UUID,
    body: OrderUpdate,
    db: Session = Depends(get_db_with_required_tenant),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    try:
        order.status = OrderStatus(body.status)
    except ValueError:
        raise HTTPException(
            status_code=400, detail=f"Invalid status. Allowed: {[s.value for s in OrderStatus]}"
        ) from None
    db.commit()
    db.refresh(order)
    request_id = getattr(request.state, "request_id", None)
    if order.status == OrderStatus.CANCELLED and settings.celery_broker_url:
        try:
            from services.worker.tasks import notify_order_cancelled

            notify_order_cancelled.delay(str(order.id), request_id=request_id)
        except Exception:
            logger.warning("Failed to enqueue notify_order_cancelled", exc_info=True)
    elif order.status == OrderStatus.CANCELLED and not settings.celery_broker_url:
        logger.info("Worker disabled; skipping notify_order_cancelled")
    return OrderResponse.model_validate(order)
