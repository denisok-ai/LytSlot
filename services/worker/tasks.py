"""
@file: tasks.py
@description: Celery tasks: ping, publish_order, process_webhook, aggregate_analytics.
@dependencies: services.worker.celery_app, db, services.api.logging_config
@created: 2025-02-19
"""

import os
from datetime import UTC, datetime
from uuid import UUID

import httpx
from sqlalchemy import text

from db.database import SessionLocal
from db.models import Order, OrderStatus, View
from services.api.logging_config import configure_json_logging, get_logger, set_request_id
from services.worker.celery_app import app

configure_json_logging()
logger = get_logger(__name__)


def _send_telegram_message(bot_token: str, chat_id: str | int, text: str) -> bool:
    """Отправить сообщение в чат/канал через Bot API. chat_id: @username или -100..."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    with httpx.Client(timeout=30.0) as client:
        r = client.post(url, json={"chat_id": chat_id, "text": text[:4096]})
    if r.status_code != 200:
        logger.warning("Telegram sendMessage failed: %s %s", r.status_code, r.text)
        return False
    return True


@app.task
def ping():
    """Тестовый таск для проверки работы воркера и очередей."""
    return {"pong": True}


@app.task(bind=True, max_retries=3)
def publish_order(self, order_id: str, request_id: str | None = None):
    """Публикация рекламы в канал (бот отправляет пост), запись в views. RLS: tenant_id."""
    set_request_id(request_id or str(self.request.id))
    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.id == UUID(order_id)).first()
        if not order:
            logger.warning("Order not found: %s", order_id)
            return
        if not order.channel:
            logger.warning("Order %s has no channel", order_id)
            return
        tenant_id = str(order.channel.tenant_id)
        db.execute(text("SELECT set_config('app.tenant_id', :tid, true)"), {"tid": tenant_id})

        # Отправка поста в Telegram (бот должен быть админом канала)
        bot_token = os.getenv("BOT_TOKEN", "").strip()
        body = order.content or {}
        msg_text = body.get("text") or "Реклама"
        if order.erid:
            msg_text += f"\n\n🛍 ERID: {order.erid}"
        if body.get("link"):
            msg_text += f"\n\n{body['link']}"

        if bot_token:
            chat_id = (
                order.channel.username
                if order.channel.username.startswith("@")
                else f"@{order.channel.username}"
            )
            if _send_telegram_message(bot_token, chat_id, msg_text):
                order.status = OrderStatus.PUBLISHED
                logger.info("Published order %s to %s", order_id, chat_id)
            else:
                raise RuntimeError("Telegram sendMessage failed")
        else:
            logger.info("BOT_TOKEN not set, skipping Telegram send for order %s", order_id)

        db.add(View(order_id=order.id, timestamp=datetime.now(UTC)))
        db.commit()
    except Exception as e:
        logger.exception("publish_order failed: %s", e)
        raise self.retry(exc=e) from e
    finally:
        db.close()


@app.task
def send_notification(telegram_id: int, text: str) -> bool:
    """Отправить личное сообщение пользователю в Telegram (chat_id = telegram_id)."""
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        logger.warning("BOT_TOKEN not set, skipping send_notification to %s", telegram_id)
        return False
    return _send_telegram_message(bot_token, telegram_id, text)


def _format_new_order_owner(order: Order) -> str:
    ch = order.channel
    ch_name = f"@{ch.username}" if ch and ch.username else "канал"
    return f"📩 Новый заказ на {ch_name}\nID: {str(order.id)[:8]}…\nСтатус: {order.status.value}"


def _format_new_order_advertiser(order: Order) -> str:
    ch = order.channel
    ch_name = f"@{ch.username}" if ch and ch.username else "канал"
    return f"✅ Ваш заказ принят\nКанал: {ch_name}\nID: {str(order.id)[:8]}…"


def _format_order_cancelled(order: Order) -> str:
    return f"❌ Заказ {str(order.id)[:8]}… отменён."


def _format_payment_received(order: Order, amount: str = "") -> str:
    return f"💰 Оплата получена по заказу {str(order.id)[:8]}…" + (
        f" Сумма: {amount}" if amount else ""
    )


@app.task(bind=True, max_retries=2)
def notify_new_order(self, order_id: str, request_id: str | None = None):
    """Уведомить владельца канала и рекламодателя о новом заказе."""
    set_request_id(request_id or str(self.request.id))
    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.id == UUID(order_id)).first()
        if not order:
            logger.warning("notify_new_order: order %s not found", order_id)
            return
        if order.channel and order.channel.tenant:
            owner_telegram_id = order.channel.tenant.telegram_id
            send_notification(owner_telegram_id, _format_new_order_owner(order))
        if order.advertiser_id:
            send_notification(order.advertiser_id, _format_new_order_advertiser(order))
    except Exception as e:
        logger.exception("notify_new_order failed: %s", e)
        raise self.retry(exc=e) from e
    finally:
        db.close()


@app.task(bind=True, max_retries=2)
def notify_order_cancelled(self, order_id: str, request_id: str | None = None):
    """Уведомить рекламодателя и владельца канала об отмене заказа."""
    set_request_id(request_id or str(self.request.id))
    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.id == UUID(order_id)).first()
        if not order:
            return
        text = _format_order_cancelled(order)
        if order.advertiser_id:
            send_notification(order.advertiser_id, text)
        if order.channel and order.channel.tenant:
            send_notification(order.channel.tenant.telegram_id, text)
    except Exception as e:
        logger.exception("notify_order_cancelled failed: %s", e)
        raise self.retry(exc=e) from e
    finally:
        db.close()


@app.task(bind=True, max_retries=2)
def notify_payment_received(self, order_id: str, amount: str = ""):
    """Уведомить о получении оплаты по заказу."""
    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.id == UUID(order_id)).first()
        if not order:
            return
        text = _format_payment_received(order, amount)
        if order.channel and order.channel.tenant:
            send_notification(order.channel.tenant.telegram_id, text)
        if order.advertiser_id:
            send_notification(order.advertiser_id, text)
    except Exception as e:
        logger.exception("notify_payment_received failed: %s", e)
        raise self.retry(exc=e) from e
    finally:
        db.close()


@app.task(bind=True)
def process_webhook(self, provider: str, data: dict):
    """Обновление статуса платежа из webhook Stripe/ЮKassa."""
    logger.info("Webhook %s: %s", provider, list(data.keys()))
    # TODO: разбор data, поиск Payment по invoice_id, обновление статуса и Order
    return {"ok": True}


@app.task
def aggregate_analytics(period: str = "day"):
    """Заглушка: агрегация метрик по периодам (для отчётов)."""
    logger.info("aggregate_analytics period=%s (stub)", period)
    return {"period": period, "done": True}
