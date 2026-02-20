#!/usr/bin/env python3
"""
@file: export-openapi.py
@description: Экспорт OpenAPI схемы FastAPI в JSON (для документации/клиентов).
@dependencies: services.api.main
@created: 2025-02-20
"""
import json
import sys
from pathlib import Path

# Корень проекта
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

from services.api.main import app

if __name__ == "__main__":
    out = root / "docs" / "openapi.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    schema = app.openapi()
    with open(out, "w", encoding="utf-8") as f:
        json.dump(schema, f, ensure_ascii=False, indent=2)
    print(f"OpenAPI schema written to {out}")
