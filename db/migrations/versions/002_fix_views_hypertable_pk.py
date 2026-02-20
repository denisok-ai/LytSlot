"""Fix views table: composite PK (timestamp, id) for TimescaleDB hypertable.

Revision ID: 002
Revises: 001
Create Date: 2025-02-20

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DROP TABLE IF EXISTS views CASCADE")
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
    op.execute("ALTER TABLE views ENABLE ROW LEVEL SECURITY")
    op.execute(
        """CREATE POLICY tenant_isolation_views ON views FOR ALL USING (
            order_id IN (SELECT id FROM orders WHERE channel_id IN (SELECT id FROM channels WHERE tenant_id::text = current_setting('app.tenant_id', true)))
        )"""
    )
    op.execute("SELECT create_hypertable('views', 'timestamp', if_not_exists => TRUE);")


def downgrade() -> None:
    op.execute("SELECT drop_hypertable('views', if_exists => TRUE);")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_views ON views")
    op.execute("ALTER TABLE views DISABLE ROW LEVEL SECURITY")
    op.drop_table("views")
