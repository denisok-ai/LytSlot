"""Initial schema: tenants, channels, slots, orders, payments, views + RLS + TimescaleDB hypertable.

Revision ID: 001
Revises:
Create Date: 2025-02-19

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;")
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("revenue_share", sa.Numeric(5, 4), nullable=False, server_default="0.2"),
        sa.Column("meta", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_tenants_telegram_id", "tenants", ["telegram_id"], unique=True)

    op.create_table(
        "channels",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("username", sa.String(255), nullable=False),
        sa.Column("slot_duration", sa.Integer(), nullable=False, server_default="3600"),
        sa.Column("price_per_slot", sa.Numeric(12, 2), nullable=False, server_default="1000"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_channels_tenant_id", "channels", ["tenant_id"])
    op.create_index("ix_channels_username", "channels", ["username"])

    op.execute(
        "DO $$ BEGIN CREATE TYPE slotstatus AS ENUM ('free', 'reserved', 'paid', 'blocked'); EXCEPTION WHEN duplicate_object THEN NULL; END $$"
    )
    slot_status = postgresql.ENUM(
        "free", "reserved", "paid", "blocked", name="slotstatus", create_type=False
    )
    op.create_table(
        "slots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "channel_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("channels.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", slot_status, nullable=False, server_default="free"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_slots_channel_id", "slots", ["channel_id"])
    op.create_index("ix_slots_datetime", "slots", ["datetime"])

    op.execute(
        "DO $$ BEGIN CREATE TYPE orderstatus AS ENUM ('draft', 'paid', 'marked', 'scheduled', 'published', 'cancelled'); EXCEPTION WHEN duplicate_object THEN NULL; END $$"
    )
    order_status = postgresql.ENUM(
        "draft",
        "paid",
        "marked",
        "scheduled",
        "published",
        "cancelled",
        name="orderstatus",
        create_type=False,
    )
    op.create_table(
        "orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("advertiser_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "channel_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("channels.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "slot_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("slots.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("content", postgresql.JSONB(), nullable=False),
        sa.Column("erid", sa.String(255), nullable=True),
        sa.Column("status", order_status, nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_orders_advertiser_id", "orders", ["advertiser_id"])
    op.create_index("ix_orders_channel_id", "orders", ["channel_id"])
    op.create_index("ix_orders_slot_id", "orders", ["slot_id"])

    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "order_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("invoice_id", sa.String(255), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_payments_order_id", "payments", ["order_id"])
    op.create_index("ix_payments_invoice_id", "payments", ["invoice_id"])

    op.create_table(
        "views",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "order_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("timestamp", "id"),
    )
    op.create_index("ix_views_order_id", "views", ["order_id"])
    op.create_index("ix_views_timestamp", "views", ["timestamp"])

    op.execute("ALTER TABLE tenants ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE channels ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE slots ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE orders ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE payments ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE views ENABLE ROW LEVEL SECURITY")

    op.execute(
        "CREATE POLICY tenant_isolation_tenants ON tenants FOR ALL USING (id::text = current_setting('app.tenant_id', true))"
    )
    op.execute(
        "CREATE POLICY tenant_isolation_channels ON channels FOR ALL USING (tenant_id::text = current_setting('app.tenant_id', true))"
    )
    op.execute(
        """CREATE POLICY tenant_isolation_slots ON slots FOR ALL USING (
            channel_id IN (SELECT id FROM channels WHERE tenant_id::text = current_setting('app.tenant_id', true))
        )"""
    )
    op.execute(
        """CREATE POLICY tenant_isolation_orders ON orders FOR ALL USING (
            channel_id IN (SELECT id FROM channels WHERE tenant_id::text = current_setting('app.tenant_id', true))
        )"""
    )
    op.execute(
        """CREATE POLICY tenant_isolation_payments ON payments FOR ALL USING (
            order_id IN (SELECT id FROM orders WHERE channel_id IN (SELECT id FROM channels WHERE tenant_id::text = current_setting('app.tenant_id', true)))
        )"""
    )
    op.execute(
        """CREATE POLICY tenant_isolation_views ON views FOR ALL USING (
            order_id IN (SELECT id FROM orders WHERE channel_id IN (SELECT id FROM channels WHERE tenant_id::text = current_setting('app.tenant_id', true)))
        )"""
    )

    op.execute("SELECT create_hypertable('views', 'timestamp', if_not_exists => TRUE);")


def downgrade() -> None:
    op.execute("SELECT drop_hypertable('views', if_exists => TRUE);")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_views ON views")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_payments ON payments")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_orders ON orders")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_slots ON slots")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_channels ON channels")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_tenants ON tenants")
    op.execute("ALTER TABLE views DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE payments DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE orders DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE slots DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE channels DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE tenants DISABLE ROW LEVEL SECURITY")
    op.drop_table("views")
    op.drop_table("payments")
    op.drop_table("orders")
    op.drop_table("slots")
    op.drop_table("channels")
    op.drop_table("tenants")
    op.execute("DROP TYPE IF EXISTS orderstatus")
    op.execute("DROP TYPE IF EXISTS slotstatus")
