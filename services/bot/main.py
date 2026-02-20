"""
@file: main.py
@description: aiogram 3 dispatcher - FSM: channel -> slot -> content -> confirm -> order.
@dependencies: aiogram, services.bot.handlers
@created: 2025-02-19
"""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from services.bot.config import settings
from services.bot.handlers.order_flow import router as order_flow_router
from services.bot.handlers.start import router as start_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    bot = Bot(token=settings.bot_token, parse_mode=ParseMode.HTML)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.include_router(start_router)
    dp.include_router(order_flow_router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
