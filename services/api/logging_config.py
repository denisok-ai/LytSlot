"""
@file: logging_config.py
@description: Structured JSON logging with request_id and tenant_id in context.
@dependencies: structlog
@created: 2025-02-20
"""

import logging
import sys
from contextvars import ContextVar
from typing import Any

import structlog

# Контекстные переменные для сквозного request_id и tenant_id в рамках запроса/задачи
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)
tenant_id_ctx: ContextVar[str | None] = ContextVar("tenant_id", default=None)


def get_request_id() -> str | None:
    """Текущий request_id (из middleware или из задачи Celery)."""
    return request_id_ctx.get()


def set_request_id(value: str | None) -> None:
    """Установить request_id в контексте (middleware или worker)."""
    request_id_ctx.set(value)


def set_tenant_id(value: str | None) -> None:
    """Установить tenant_id в контексте (для логов)."""
    tenant_id_ctx.set(value)


def _add_context(
    logger: logging.Logger, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Добавить request_id и tenant_id из contextvars в каждую запись лога."""
    rid = request_id_ctx.get()
    if rid is not None:
        event_dict["request_id"] = rid
    tid = tenant_id_ctx.get()
    if tid is not None:
        event_dict["tenant_id"] = tid
    return event_dict


def configure_json_logging() -> None:
    """
    Настроить structlog: JSON в stdout, уровень INFO.
    После вызова использовать structlog.get_logger() с request_id/tenant_id.
    """
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            _add_context,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None):
    """Логгер с контекстом request_id/tenant_id. name — имя модуля (__name__)."""
    return structlog.get_logger(name)
