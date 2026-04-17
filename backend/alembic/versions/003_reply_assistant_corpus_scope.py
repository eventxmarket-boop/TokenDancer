"""reply assistant corpus scope

Revision ID: 003_reply_assistant_corpus_scope
Revises: 002_reply_assistant_corpora
Create Date: 2026-04-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003_reply_assistant_corpus_scope"
down_revision: Union[str, None] = "002_reply_assistant_corpora"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "reply_assistant_corpora",
        sa.Column("target_person_type", sa.String(length=32), nullable=False, server_default="any"),
    )
    op.add_column(
        "reply_assistant_corpora",
        sa.Column("scene_type", sa.String(length=32), nullable=False, server_default="any"),
    )
    op.alter_column(
        "reply_assistant_corpora",
        "corpus_type",
        existing_type=sa.String(length=64),
        type_=sa.String(length=128),
        existing_nullable=False,
        server_default="通用",
    )


def downgrade() -> None:
    op.alter_column(
        "reply_assistant_corpora",
        "corpus_type",
        existing_type=sa.String(length=128),
        type_=sa.String(length=64),
        existing_nullable=False,
        server_default="高情商回复",
    )
    op.drop_column("reply_assistant_corpora", "scene_type")
    op.drop_column("reply_assistant_corpora", "target_person_type")
