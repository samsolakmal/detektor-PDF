"""Enable pgvector extension in PostgreSQL.

Revision ID: 20261112_0002
Revises: 20261112_0001
Create Date: 2026-11-12
"""

from alembic import op


revision = "20261112_0002"
down_revision = "20261112_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Install the extension only; this project does not create embeddings or vector columns.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    # Keep the database-wide extension installed; other tables may depend on it.
    pass
