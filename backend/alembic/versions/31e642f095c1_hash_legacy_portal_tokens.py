"""Hash previously issued patient portal tokens.

Revision ID: 31e642f095c1
Revises: 62baca9db874
"""
from hashlib import sha256
import re

from alembic import op
import sqlalchemy as sa

revision = "31e642f095c1"
down_revision = "62baca9db874"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    rows = connection.execute(sa.text("SELECT id, portal_token FROM claims WHERE portal_token IS NOT NULL")).all()
    for claim_id, token in rows:
        if not re.fullmatch(r"[0-9a-f]{64}", token or ""):
            digest = sha256(token.encode("utf-8")).hexdigest()
            connection.execute(
                sa.text("UPDATE claims SET portal_token = :digest WHERE id = :claim_id"),
                {"digest": digest, "claim_id": claim_id},
            )


def downgrade() -> None:
    # Hashes are one-way by design; never convert them back to credentials.
    pass
