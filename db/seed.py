"""
@file: seed.py
@description: Тестовые данные для всех сущностей (tenant, channels, slots, orders, views, api_keys).
@dependencies: db.database, db.models
@created: 2025-02-19
"""

import hashlib
import uuid
from contextlib import suppress
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from db.database import SessionLocal
from db.models import (
    ApiKey,
    Channel,
    Order,
    OrderStatus,
    Slot,
    SlotStatus,
    Tenant,
    View,
)


def _hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


DEMO_TELEGRAM_ID = 123456789


def seed_demo() -> None:
    """Демо-tenant 123456789: каналы, слоты, заказы, просмотры, api_keys."""
    db = SessionLocal()
    try:
        t = db.query(Tenant).filter(Tenant.telegram_id == DEMO_TELEGRAM_ID).first()
        if t:
            # Tenant уже есть — дополняем недостающими каналами, заказами, просмотрами, api_key
            _ensure_demo_data(db, t)
            db.commit()
            print(
                "Seed OK (обновлён): данные для tenant 123456789 добавлены/проверены. "
                "Войдите с telegram_id=123456789."
            )
            return

        tenant = Tenant(
            id=uuid.uuid4(),
            telegram_id=DEMO_TELEGRAM_ID,
            name="Demo Tenant",
            revenue_share=Decimal("0.2"),
        )
        db.add(tenant)
        db.flush()

        # Канал 1
        ch1 = Channel(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            username="demo_channel",
            slot_duration=3600,
            price_per_slot=Decimal("1000"),
            is_active=True,
        )
        db.add(ch1)
        db.flush()

        # Канал 2
        ch2 = Channel(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            username="tech_reviews_ru",
            slot_duration=1800,
            price_per_slot=Decimal("2500"),
            is_active=True,
        )
        db.add(ch2)
        db.flush()

        # Канал 3 — для проверки фильтра в Аналитике и списка каналов
        ch3 = Channel(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            username="gadgets_news",
            slot_duration=3600,
            price_per_slot=Decimal("1500"),
            is_active=True,
        )
        db.add(ch3)
        db.flush()

        base = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
        slots_ch1 = []
        for i in range(14):
            status = SlotStatus.FREE
            if i == 5:
                status = SlotStatus.BLOCKED
            elif i == 6:
                status = SlotStatus.RESERVED
            slot = Slot(
                id=uuid.uuid4(),
                channel_id=ch1.id,
                datetime=base + timedelta(days=i, hours=10),
                status=status,
            )
            db.add(slot)
            db.flush()
            slots_ch1.append(slot)

        slots_ch2 = []
        for i in range(7):
            slot = Slot(
                id=uuid.uuid4(),
                channel_id=ch2.id,
                datetime=base + timedelta(days=i, hours=14),
                status=SlotStatus.FREE if i != 1 else SlotStatus.PAID,
            )
            db.add(slot)
            db.flush()
            slots_ch2.append(slot)

        slots_ch3 = []
        for i in range(5):
            slot = Slot(
                id=uuid.uuid4(),
                channel_id=ch3.id,
                datetime=base + timedelta(days=i, hours=18),
                status=SlotStatus.FREE,
            )
            db.add(slot)
            db.flush()
            slots_ch3.append(slot)

        # Заказы — все статусы для экрана «Заказы»
        order1 = Order(
            id=uuid.uuid4(),
            advertiser_id=123456789,
            channel_id=ch1.id,
            slot_id=slots_ch1[0].id,
            content={"text": "Реклама магазина электроники", "link": "https://example.com/shop"},
            erid="2VtzqwXyRd",
            status=OrderStatus.PUBLISHED,
        )
        db.add(order1)
        db.flush()
        slots_ch1[0].status = SlotStatus.PAID
        db.flush()

        order2 = Order(
            id=uuid.uuid4(),
            advertiser_id=111222333,
            channel_id=ch1.id,
            slot_id=slots_ch1[1].id,
            content={"text": "Скидка 20% по промокоду", "link": "https://promo.example.com"},
            erid=None,
            status=OrderStatus.DRAFT,
        )
        db.add(order2)
        db.flush()

        order3 = Order(
            id=uuid.uuid4(),
            advertiser_id=123456789,
            channel_id=ch2.id,
            slot_id=slots_ch2[0].id,
            content={"text": "Новый курс по Python"},
            erid="2VtzqwXyRf",
            status=OrderStatus.PAID,
        )
        db.add(order3)
        db.flush()

        order4 = Order(
            id=uuid.uuid4(),
            advertiser_id=555666777,
            channel_id=ch1.id,
            slot_id=slots_ch1[2].id,
            content={"text": "Маркировка получена, ожидаем публикации"},
            erid="2VtzqwXyRa",
            status=OrderStatus.MARKED,
        )
        db.add(order4)
        db.flush()

        order5 = Order(
            id=uuid.uuid4(),
            advertiser_id=888999000,
            channel_id=ch1.id,
            slot_id=slots_ch1[3].id,
            content={"text": "Заплановано на среду"},
            erid="2VtzqwXyRb",
            status=OrderStatus.SCHEDULED,
        )
        db.add(order5)
        db.flush()

        order6 = Order(
            id=uuid.uuid4(),
            advertiser_id=111222333,
            channel_id=ch2.id,
            slot_id=slots_ch2[1].id,
            content={"text": "Отменённый заказ"},
            erid=None,
            status=OrderStatus.CANCELLED,
        )
        db.add(order6)
        db.flush()

        order7 = Order(
            id=uuid.uuid4(),
            advertiser_id=123456789,
            channel_id=ch3.id,
            slot_id=slots_ch3[0].id,
            content={"text": "Реклама в канале гаджетов"},
            erid="2VtzqwXyRc",
            status=OrderStatus.PUBLISHED,
        )
        db.add(order7)
        db.flush()

        # Просмотры за последние 30+ дней — для графика «Аналитика»
        def add_views_for_order(order_id, days_back=35, base_count=2, peak_day=5):
            for d in range(days_back):
                day_start = base - timedelta(days=d)
                n = base_count + (peak_day - min(d, peak_day)) + (d % 4)
                for _ in range(n):
                    v = View(
                        id=uuid.uuid4(),
                        order_id=order_id,
                        timestamp=day_start + timedelta(hours=10 + (d % 12), minutes=d * 2),
                    )
                    db.add(v)

        add_views_for_order(order1.id)
        add_views_for_order(order3.id, days_back=25, base_count=1, peak_day=3)
        add_views_for_order(order7.id, days_back=20, base_count=0, peak_day=2)
        db.flush()

        # API-ключи для экрана «Настройки»
        try:
            db.add(
                ApiKey(
                    id=uuid.uuid4(),
                    tenant_id=tenant.id,
                    key_hash=_hash_key("lytslot_test_seed_key_do_not_use"),
                    name="Тестовый ключ (seed)",
                )
            )
            db.add(
                ApiKey(
                    id=uuid.uuid4(),
                    tenant_id=tenant.id,
                    key_hash=_hash_key("lytslot_second_demo_key"),
                    name="Второй ключ для проверки",
                )
            )
        except Exception:
            pass  # миграция 003 могла не быть применена

        db.commit()
        print(
            "Seed OK: tenant 123456789, 3 channels, slots, 7 orders, просмотры 30+ дней, "
            "2 api_keys. Войдите с telegram_id=123456789."
        )
    except Exception as e:
        db.rollback()
        print(f"Seed ошибка: {e}")
        raise
    finally:
        db.close()


def _ensure_demo_data(db, tenant) -> None:
    """Добавляет каналы, слоты, заказы, просмотры за 30 дней, api_keys если их ещё нет."""
    channels = db.query(Channel).filter(Channel.tenant_id == tenant.id).all()
    ch1 = ch2 = ch3 = None
    for c in channels:
        if c.username == "demo_channel":
            ch1 = c
        elif c.username == "tech_reviews_ru":
            ch2 = c
        elif c.username == "gadgets_news":
            ch3 = c
    base = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)

    if not ch1:
        ch1 = Channel(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            username="demo_channel",
            slot_duration=3600,
            price_per_slot=Decimal("1000"),
            is_active=True,
        )
        db.add(ch1)
        db.flush()
    if not ch2:
        ch2 = Channel(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            username="tech_reviews_ru",
            slot_duration=1800,
            price_per_slot=Decimal("2500"),
            is_active=True,
        )
        db.add(ch2)
        db.flush()
    if not ch3:
        ch3 = Channel(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            username="gadgets_news",
            slot_duration=3600,
            price_per_slot=Decimal("1500"),
            is_active=True,
        )
        db.add(ch3)
        db.flush()

    slots_ch1 = db.query(Slot).filter(Slot.channel_id == ch1.id).order_by(Slot.datetime).all()
    if len(slots_ch1) < 14:
        for i in range(14):
            dt = base + timedelta(days=i, hours=10)
            if not any(s.datetime == dt for s in slots_ch1):
                status = (
                    SlotStatus.BLOCKED
                    if i == 5
                    else (SlotStatus.RESERVED if i == 6 else SlotStatus.FREE)
                )
                slot = Slot(id=uuid.uuid4(), channel_id=ch1.id, datetime=dt, status=status)
                db.add(slot)
                db.flush()
                slots_ch1.append(slot)
    slots_ch2 = db.query(Slot).filter(Slot.channel_id == ch2.id).order_by(Slot.datetime).all()
    if len(slots_ch2) < 7:
        for i in range(7):
            dt = base + timedelta(days=i, hours=14)
            if not any(s.datetime == dt for s in slots_ch2):
                slot = Slot(id=uuid.uuid4(), channel_id=ch2.id, datetime=dt, status=SlotStatus.FREE)
                db.add(slot)
                db.flush()
                slots_ch2.append(slot)
    slots_ch3 = db.query(Slot).filter(Slot.channel_id == ch3.id).order_by(Slot.datetime).all()
    if len(slots_ch3) < 5:
        for i in range(5):
            dt = base + timedelta(days=i, hours=18)
            if not any(s.datetime == dt for s in slots_ch3):
                slot = Slot(id=uuid.uuid4(), channel_id=ch3.id, datetime=dt, status=SlotStatus.FREE)
                db.add(slot)
                db.flush()
                slots_ch3.append(slot)

    slots_ch1 = db.query(Slot).filter(Slot.channel_id == ch1.id).order_by(Slot.datetime).all()
    slots_ch2 = db.query(Slot).filter(Slot.channel_id == ch2.id).order_by(Slot.datetime).all()
    slots_ch3 = db.query(Slot).filter(Slot.channel_id == ch3.id).order_by(Slot.datetime).all()
    orders_all = db.query(Order).filter(Order.channel_id.in_([ch1.id, ch2.id, ch3.id])).all()
    statuses_present = {o.status for o in orders_all}

    def add_views_for_order(order_id, days_back=35, base_count=2, peak_day=5):
        for d in range(days_back):
            day_start = base - timedelta(days=d)
            n = base_count + (peak_day - min(d, peak_day)) + (d % 4)
            for _ in range(n):
                v = View(
                    id=uuid.uuid4(),
                    order_id=order_id,
                    timestamp=day_start + timedelta(hours=10 + (d % 12), minutes=d * 2),
                )
                db.add(v)

    # Добавляем заказы со всеми статусами, если их нет
    if OrderStatus.PUBLISHED not in statuses_present and len(slots_ch1) >= 1:
        o1 = Order(
            id=uuid.uuid4(),
            advertiser_id=DEMO_TELEGRAM_ID,
            channel_id=ch1.id,
            slot_id=slots_ch1[0].id,
            content={"text": "Реклама магазина электроники", "link": "https://example.com/shop"},
            erid="2VtzqwXyRd",
            status=OrderStatus.PUBLISHED,
        )
        db.add(o1)
        db.flush()
        add_views_for_order(o1.id)
    else:
        o1 = (
            db.query(Order)
            .filter(Order.channel_id == ch1.id, Order.status == OrderStatus.PUBLISHED)
            .first()
        )

    if OrderStatus.DRAFT not in statuses_present and len(slots_ch1) >= 2:
        db.add(
            Order(
                id=uuid.uuid4(),
                advertiser_id=111222333,
                channel_id=ch1.id,
                slot_id=slots_ch1[1].id,
                content={"text": "Скидка 20% по промокоду", "link": "https://promo.example.com"},
                erid=None,
                status=OrderStatus.DRAFT,
            )
        )
        db.flush()
    if OrderStatus.PAID not in statuses_present and len(slots_ch2) >= 1:
        o3 = Order(
            id=uuid.uuid4(),
            advertiser_id=DEMO_TELEGRAM_ID,
            channel_id=ch2.id,
            slot_id=slots_ch2[0].id,
            content={"text": "Новый курс по Python"},
            erid="2VtzqwXyRf",
            status=OrderStatus.PAID,
        )
        db.add(o3)
        db.flush()
        add_views_for_order(o3.id, days_back=25, base_count=1, peak_day=3)
    if OrderStatus.MARKED not in statuses_present and len(slots_ch1) >= 3:
        db.add(
            Order(
                id=uuid.uuid4(),
                advertiser_id=555666777,
                channel_id=ch1.id,
                slot_id=slots_ch1[2].id,
                content={"text": "Маркировка получена"},
                erid="2VtzqwXyRa",
                status=OrderStatus.MARKED,
            )
        )
        db.flush()
    if OrderStatus.SCHEDULED not in statuses_present and len(slots_ch1) >= 4:
        db.add(
            Order(
                id=uuid.uuid4(),
                advertiser_id=888999000,
                channel_id=ch1.id,
                slot_id=slots_ch1[3].id,
                content={"text": "Заплановано на среду"},
                erid="2VtzqwXyRb",
                status=OrderStatus.SCHEDULED,
            )
        )
        db.flush()
    if OrderStatus.CANCELLED not in statuses_present and len(slots_ch2) >= 2:
        db.add(
            Order(
                id=uuid.uuid4(),
                advertiser_id=111222333,
                channel_id=ch2.id,
                slot_id=slots_ch2[1].id,
                content={"text": "Отменённый заказ"},
                erid=None,
                status=OrderStatus.CANCELLED,
            )
        )
        db.flush()
    if len(slots_ch3) >= 1:
        orders_ch3 = db.query(Order).filter(Order.channel_id == ch3.id).count()
        if orders_ch3 == 0:
            o7 = Order(
                id=uuid.uuid4(),
                advertiser_id=DEMO_TELEGRAM_ID,
                channel_id=ch3.id,
                slot_id=slots_ch3[0].id,
                content={"text": "Реклама в канале гаджетов"},
                erid="2VtzqwXyRc",
                status=OrderStatus.PUBLISHED,
            )
            db.add(o7)
            db.flush()
            add_views_for_order(o7.id, days_back=20, base_count=0, peak_day=2)

    # Доп. просмотры, если общее число маленькое (для графика аналитики)
    views_count = db.query(View).count()
    order_for_views = o1 or db.query(Order).filter(Order.channel_id == ch1.id).first()
    if views_count < 100 and order_for_views is not None:
        add_views_for_order(order_for_views.id)

    api_keys_count = db.query(ApiKey).filter(ApiKey.tenant_id == tenant.id).count()
    if api_keys_count == 0:
        with suppress(Exception):
            db.add(
                ApiKey(
                    id=uuid.uuid4(),
                    tenant_id=tenant.id,
                    key_hash=_hash_key("lytslot_test_seed_key_do_not_use"),
                    name="Тестовый ключ (seed)",
                )
            )
    if api_keys_count < 2:
        with suppress(Exception):
            db.add(
                ApiKey(
                    id=uuid.uuid4(),
                    tenant_id=tenant.id,
                    key_hash=_hash_key("lytslot_second_demo_key"),
                    name="Второй ключ для проверки",
                )
            )


def seed_extra() -> None:
    """Добавляет ещё слоты и просмотры за последние дни к demo-tenant (idempotent)."""
    db = SessionLocal()
    try:
        t = db.query(Tenant).filter(Tenant.telegram_id == DEMO_TELEGRAM_ID).first()
        if not t:
            print("Demo tenant not found. Run seed_demo() first.")
            db.close()
            return

        channels = db.query(Channel).filter(Channel.tenant_id == t.id).all()
        if not channels:
            print("No channels for demo tenant.")
            db.close()
            return

        base = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)

        # Ещё слоты на первом канале
        ch = channels[0]
        for i in range(14, 21):
            existing = (
                db.query(Slot)
                .filter(
                    Slot.channel_id == ch.id,
                    Slot.datetime == base + timedelta(days=i, hours=10),
                )
                .first()
            )
            if not existing:
                db.add(
                    Slot(
                        id=uuid.uuid4(),
                        channel_id=ch.id,
                        datetime=base + timedelta(days=i, hours=10),
                        status=SlotStatus.FREE,
                    )
                )

        # Просмотры за последние 10 дней по нескольким заказам (для графика аналитики)
        orders = (
            db.query(Order).filter(Order.channel_id.in_([c.id for c in channels])).limit(5).all()
        )
        for order in orders:
            for d in range(10):
                for _ in range(2 + (d % 5)):
                    db.add(
                        View(
                            id=uuid.uuid4(),
                            order_id=order.id,
                            timestamp=base
                            - timedelta(days=d)
                            + timedelta(hours=8 + d, minutes=d * 7),
                        )
                    )

        db.commit()
        print("Seed extra OK: добавлены слоты и просмотры.")
    finally:
        db.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "extra":
        seed_extra()
    else:
        seed_demo()
