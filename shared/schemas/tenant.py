"""
@file: tenant.py
@description: Tenant-scoped base and tenant schemas.
@dependencies: pydantic
@created: 2025-02-19
"""

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BaseTenantModel(BaseModel):
    """Mixin: all tenant-scoped responses include tenant_id for consistency."""

    model_config = ConfigDict(from_attributes=True)

    tenant_id: UUID | None = None
