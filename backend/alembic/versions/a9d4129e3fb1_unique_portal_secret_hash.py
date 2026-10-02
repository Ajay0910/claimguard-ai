"""Enforce unique patient portal secret hashes for idempotent submissions.

Revision ID: a9d4129e3fb1
Revises: 8c306db120c5
"""
from alembic import op
import sqlalchemy as sa

revision = "a9d4129e3fb1"
down_revision = "8c306db120c5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    indexes = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("claims")}
    if "ix_claims_portal_token" not in indexes:
        op.create_index("ix_claims_portal_token", "claims", ["portal_token"], unique=True)


def downgrade() -> None:
    indexes = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("claims")}
    if "ix_claims_portal_token" in indexes:
        op.drop_index("ix_claims_portal_token", table_name="claims")
