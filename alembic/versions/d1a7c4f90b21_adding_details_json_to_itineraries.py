"""adding details json to itineraries

Revision ID: d1a7c4f90b21
Revises: b003aed18c5a
Create Date: 2026-09-20

Stores the full structured day emitted by the AI itinerary workflow (dates,
per-activity times, locations and tips) which the normalised activities table
has no columns for.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "d1a7c4f90b21"
down_revision: Union[str, Sequence[str], None] = "b003aed18c5a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "itineraries",
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("itineraries", "details")
