"""
@file: states.py
@description: FSM states for order flow: channel -> slot -> content -> confirm.
@dependencies: aiogram
@created: 2025-02-20
"""

from aiogram.fsm.state import State, StatesGroup


class OrderStates(StatesGroup):
    choosing_channel = State()
    choosing_slot = State()
    entering_content = State()
    confirm = State()
