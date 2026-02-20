"""
@file: order_flow.py
@description: FSM: выбор канала -> слот -> текст рекламы -> подтверждение заказа.
@dependencies: aiogram, services.bot.api_client, services.bot.handlers.states
@created: 2025-02-20
"""

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from services.bot.api_client import create_order, get_channels, get_slots, get_token
from services.bot.handlers.states import OrderStates

logger = logging.getLogger(__name__)
router = Router()


def _channel_keyboard(channels: list[dict]) -> InlineKeyboardMarkup:
    rows = []
    for ch in channels:
        rows.append(
            [InlineKeyboardButton(text=f"@{ch['username']}", callback_data=f"channel:{ch['id']}")]
        )
    rows.append([InlineKeyboardButton(text="Отмена", callback_data="order_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _slot_keyboard(slots: list[dict]) -> InlineKeyboardMarkup:
    rows = []
    for s in slots:
        if s.get("status") != "free":
            continue
        dt = s.get("datetime", "")
        try:
            if "T" in dt:
                d = datetime.fromisoformat(dt.replace("Z", "+00:00"))
            else:
                d = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
            label = d.strftime("%d.%m %H:%M")
        except Exception:
            label = dt[:16] if len(dt) > 16 else dt
        rows.append([InlineKeyboardButton(text=label, callback_data=f"slot:{s['id']}")])
    rows.append([InlineKeyboardButton(text="Назад к каналам", callback_data="order_back_channels")])
    rows.append([InlineKeyboardButton(text="Отмена", callback_data="order_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Подтвердить заказ", callback_data="order_confirm")],
            [InlineKeyboardButton(text="Отмена", callback_data="order_cancel")],
        ]
    )


@router.callback_query(F.data == "slot_picker")
async def start_order_flow(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    user_id = callback.from_user.id if callback.from_user else 0
    token = await get_token(user_id)
    if not token:
        await callback.message.edit_text(
            "Не удалось авторизоваться. Убедитесь, что API запущен и "
            "ENABLE_DEV_LOGIN=true (для разработки)."
        )
        return
    channels = await get_channels(token)
    if not channels:
        await callback.message.edit_text(
            "У вас пока нет каналов. Добавьте канал в веб-кабинете LytSlot, "
            "затем снова выберите «Выбрать слот»."
        )
        return
    await state.update_data(token=token)
    await state.set_state(OrderStates.choosing_channel)
    await callback.message.edit_text("Выберите канал:", reply_markup=_channel_keyboard(channels))


@router.callback_query(F.data.startswith("channel:"), OrderStates.choosing_channel)
async def on_channel_selected(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    channel_id = callback.data.replace("channel:", "").strip()
    if not channel_id:
        return
    try:
        UUID(channel_id)
    except ValueError:
        return
    data = await state.get_data()
    token = data.get("token")
    if not token:
        await state.clear()
        await callback.message.edit_text("Сессия истекла. Нажмите /start.")
        return
    now = datetime.now(UTC)
    date_from = now
    date_to = now + timedelta(days=14)
    slots = await get_slots(token, UUID(channel_id), date_from=date_from, date_to=date_to)
    free_slots = [s for s in slots if s.get("status") == "free"]
    await state.update_data(channel_id=channel_id)
    await state.set_state(OrderStates.choosing_slot)
    if not free_slots:
        await callback.message.edit_text(
            "В этом канале нет свободных слотов на ближайшие 14 дней. "
            "Выберите другой канал или добавьте слоты в веб-кабинете.",
            reply_markup=_channel_keyboard(await get_channels(token)),
        )
        await state.set_state(OrderStates.choosing_channel)
        return
    await callback.message.edit_text(
        "Выберите слот (дата и время):", reply_markup=_slot_keyboard(free_slots)
    )


@router.callback_query(F.data == "order_back_channels", OrderStates.choosing_slot)
async def back_to_channels(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    token = data.get("token")
    if not token:
        await state.clear()
        await callback.message.edit_text("Сессия истекла. Нажмите /start.")
        return
    channels = await get_channels(token)
    await state.set_state(OrderStates.choosing_channel)
    await callback.message.edit_text("Выберите канал:", reply_markup=_channel_keyboard(channels))


@router.callback_query(F.data.startswith("slot:"), OrderStates.choosing_slot)
async def on_slot_selected(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    slot_id = callback.data.replace("slot:", "").strip()
    if not slot_id:
        return
    try:
        UUID(slot_id)
    except ValueError:
        return
    await state.update_data(slot_id=slot_id)
    await state.set_state(OrderStates.entering_content)
    await callback.message.edit_text("Введите текст рекламы одним сообщением (можно с ссылкой):")


@router.message(OrderStates.entering_content, F.text)
async def on_content_entered(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if not text:
        await message.answer("Введите непустой текст.")
        return
    await state.update_data(content_text=text)
    data = await state.get_data()
    channel_id = data.get("channel_id", "")
    slot_id = data.get("slot_id", "")
    await state.set_state(OrderStates.confirm)
    text_preview = f"{text[:200]}{'…' if len(text) > 200 else ''}"
    await message.answer(
        f"Проверьте заказ:\n\nКанал/слот: {channel_id[:8]}… / {slot_id[:8]}…\n"
        f"Текст: {text_preview}\n\nПодтвердить?",
        reply_markup=_confirm_keyboard(),
    )


@router.callback_query(F.data == "order_confirm", OrderStates.confirm)
async def on_order_confirm(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    token = data.get("token")
    channel_id = data.get("channel_id")
    slot_id = data.get("slot_id")
    content_text = data.get("content_text", "Реклама")
    if not all([token, channel_id, slot_id]):
        await state.clear()
        await callback.message.edit_text("Данные заказа потеряны. Начните с /start.")
        return
    try:
        order = await create_order(
            token,
            UUID(channel_id),
            UUID(slot_id),
            {"text": content_text},
            erid=None,
        )
        await state.clear()
        await callback.message.edit_text(f"Заказ создан. ID: {order.get('id', '')[:8]}…")
    except Exception as e:
        logger.exception("create_order failed")
        await callback.message.edit_text(f"Ошибка создания заказа: {e}")


@router.callback_query(F.data == "order_cancel")
async def on_order_cancel(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    from services.bot.handlers.start import _main_menu_kb

    await callback.message.edit_text(
        "LytSlot Pro. Выберите действие:", reply_markup=_main_menu_kb()
    )
