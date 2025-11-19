"""Add LLM result flag and make images nullable.

Revision ID: 1c2b3a4d5e6f
Revises: 0b7a6714b29d
Create Date: 2025-11-05 05:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1c2b3a4d5e6f"
down_revision: Union[str, Sequence[str], None] = "0b7a6714b29d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("sudoku", sa.Column("llm_is_correct", sa.Boolean(), nullable=True))
    op.add_column("sudoku", sa.Column("llm_checked_at", sa.DateTime(), nullable=True))

    op.execute("DROP TABLE IF EXISTS reasoner_accuracy")

    with op.batch_alter_table("sudoku_image", schema=None) as batch_op:
        batch_op.alter_column(
            "content",
            existing_type=sa.LargeBinary(),
            nullable=True,
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("sudoku_image", schema=None) as batch_op:
        batch_op.alter_column(
            "content",
            existing_type=sa.LargeBinary(),
            nullable=False,
        )

    op.execute("DROP TABLE IF EXISTS reasoner_accuracy")
    op.create_table(
        "reasoner_accuracy",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("technique", sa.String(length=64), nullable=False),
        sa.Column("sample_size", sa.Integer(), nullable=False),
        sa.Column("success_count", sa.Integer(), nullable=False),
        sa.Column("accuracy", sa.Float(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("technique", name="uq_reasoner_accuracy_technique"),
    )

    with op.batch_alter_table("sudoku", schema=None) as batch_op:
        batch_op.drop_column("llm_checked_at")
        batch_op.drop_column("llm_is_correct")
