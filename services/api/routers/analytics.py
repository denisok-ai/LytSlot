"""
@file: analytics.py
@description: Analytics - views by day, summary (tenant-scoped).
@dependencies: fastapi, db.models, sqlalchemy
@created: 2025-02-20
"""

from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from db.models import Channel, Order, View
from services.api.deps import get_db_with_required_tenant

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/views", summary="Просмотры по дням")
def get_views_by_day(
    date_from: datetime | None = Query(None, description="Начало периода (включительно)"),
    date_to: datetime | None = Query(None, description="Конец периода (включительно)"),
    channel_id: UUID | None = Query(None, description="Фильтр по каналу"),
    db: Session = Depends(get_db_with_required_tenant),
):
    """Агрегат просмотров по дням из таблицы views. По умолчанию — последние 30 дней."""
    end = date_to or datetime.utcnow()
    start = date_from or (end - timedelta(days=30))
    if start > end:
        start, end = end, start

    q = (
        db.query(
            func.date_trunc("day", View.timestamp).label("day"),
            func.count(View.id).label("count"),
        )
        .join(Order, View.order_id == Order.id)
        .filter(View.timestamp >= start, View.timestamp < end + timedelta(days=1))
    )
    if channel_id is not None:
        q = q.filter(Order.channel_id == channel_id)
    q = q.group_by(func.date_trunc("day", View.timestamp)).order_by(
        func.date_trunc("day", View.timestamp)
    )

    rows = q.all()
    out = []
    for r in rows:
        day = r.day
        date_str = day.isoformat()[:10] if hasattr(day, "isoformat") else str(day)[:10]
        out.append({"date": date_str, "views": r.count})
    return out


@router.get("/summary", summary="Сводка (каналы, заказы, просмотры, выручка)")
def get_summary(db: Session = Depends(get_db_with_required_tenant)):
    """Сводные счётчики tenant: channels_count, orders_count, views_total, revenue_total."""
    channels_count = db.query(Channel).count()
    orders_count = db.query(Order).count()
    views_total = db.query(func.count(View.id)).scalar() or 0
    return {
        "channels_count": channels_count,
        "orders_count": orders_count,
        "views_total": views_total,
        "revenue_total": 0,
    }
