"""
@file: start.py
@description: /start and main menu - Мои каналы, Выбрать слот, Статистика.
@dependencies: aiogram, services.bot.api_client
@created: 2025-02-19
"""

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from services.bot.api_client import get_channels, get_token

router = Router()


def _main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Мои каналы", callback_data="channels")],
            [InlineKeyboardButton(text="Выбрать слот", callback_data="slot_picker")],
            [InlineKeyboardButton(text="Статистика", callback_data="stats")],
        ]
    )


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("LytSlot Pro. Выберите действие:", reply_markup=_main_menu_kb())


@router.callback_query(F.data == "channels")
async def show_channels(callback: CallbackQuery):
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
            "У вас пока нет каналов. Добавьте канал в веб-кабинете LytSlot."
        )
        return
    lines = ["Ваши каналы:\n"] + [f"• @{ch['username']}" for ch in channels]
    await callback.message.edit_text("\n".join(lines), reply_markup=_main_menu_kb())


@router.callback_query(F.data == "stats")
async def show_stats(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        "Статистика и аналитика доступны в веб-кабинете: откройте дашборд в браузере.",
        reply_markup=_main_menu_kb(),
    )
