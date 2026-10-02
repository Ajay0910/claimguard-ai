"""Allow unknown analysis impact to remain null.

Revision ID: 8c306db120c5
Revises: 31e642f095c1
"""
from alembic import op
import sqlalchemy as sa

revision = "8c306db120c5"
down_revision = "31e642f095c1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "UPDATE analysis_runs SET total_monetary_impact = NULL "
        "WHERE overall_status IN ('EXTRACTION_FAILED', 'INSUFFICIENT_EVIDENCE', 'REVIEW_RECOMMENDED', 'BLOCKED')"
    )
    with op.batch_alter_table("analysis_runs") as batch:
        batch.alter_column("total_monetary_impact", existing_type=sa.Float(), nullable=True)


def downgrade() -> None:
    op.execute("UPDATE analysis_runs SET total_monetary_impact = 0.0 WHERE total_monetary_impact IS NULL")
    with op.batch_alter_table("analysis_runs") as batch:
        batch.alter_column("total_monetary_impact", existing_type=sa.Float(), nullable=False)
