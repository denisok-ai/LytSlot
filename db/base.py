"""
@file: base.py
@description: SQLAlchemy declarative base and session factory for LytSlot Pro.
@dependencies: sqlalchemy
@created: 2025-02-19
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base for all models."""

    pass
