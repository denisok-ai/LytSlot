"""
@file: database.py
@description: Sync engine and session factory. API uses deps.get_db from services.api.deps.
@dependencies: sqlalchemy, db.base, db.models
@created: 2025-02-19
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db import models  # noqa: F401 - register models

DATABASE_URL_SYNC = os.getenv(
    "DATABASE_URL_SYNC", "postgresql://lytslot:lytslot@localhost:5432/lytslot"
)

engine = create_engine(DATABASE_URL_SYNC, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
