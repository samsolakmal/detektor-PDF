"""Create persistent analysis history.

Revision ID: 20261112_0001
Revises:
Create Date: 2026-11-12
"""

from alembic import op
import sqlalchemy as sa


revision = "20261112_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Store only analysis summaries and findings, never the source document or extracted text.
    op.create_table(
        "analysis_records",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("document_type", sa.String(length=10), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("word_count", sa.Integer(), nullable=False),
        sa.Column("findings", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "document_type IN ('pdf', 'docx')", name="ck_analysis_document_type"
        ),
        sa.CheckConstraint("score BETWEEN 0 AND 100", name="ck_analysis_score_range"),
        sa.CheckConstraint("word_count >= 0", name="ck_analysis_word_count"),
    )
    op.create_index(
        "ix_analysis_records_created_at",
        "analysis_records",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_analysis_records_created_at", table_name="analysis_records")
    op.drop_table("analysis_records")
