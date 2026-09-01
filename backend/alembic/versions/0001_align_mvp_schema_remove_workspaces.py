"""Align MVP Schema and Remove Workspace Entity

Revision ID: 0001_align_mvp_schema
Revises: 
Create Date: 2026-09-01 03:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0001_align_mvp_schema"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop obsolete workspace_id columns and workspaces table, ensuring MVP alignment."""
    # 1. Drop foreign keys and columns from existing tables if present
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # Drop from personas
    if "personas" in existing_tables:
        columns = [col["name"] for col in inspector.get_columns("personas")]
        if "workspace_id" in columns:
            op.execute("ALTER TABLE personas DROP CONSTRAINT IF EXISTS personas_workspace_id_fkey CASCADE")
            op.drop_column("personas", "workspace_id")

    # Drop from documents
    if "documents" in existing_tables:
        columns = [col["name"] for col in inspector.get_columns("documents")]
        if "workspace_id" in columns:
            op.execute("ALTER TABLE documents DROP CONSTRAINT IF EXISTS documents_workspace_id_fkey CASCADE")
            op.drop_column("documents", "workspace_id")

    # Drop from collection_links
    if "collection_links" in existing_tables:
        columns = [col["name"] for col in inspector.get_columns("collection_links")]
        if "workspace_id" in columns:
            op.execute("ALTER TABLE collection_links DROP CONSTRAINT IF EXISTS collection_links_workspace_id_fkey CASCADE")
            op.drop_column("collection_links", "workspace_id")

    # Drop from webhook_configs
    if "webhook_configs" in existing_tables:
        columns = [col["name"] for col in inspector.get_columns("webhook_configs")]
        if "workspace_id" in columns:
            op.execute("ALTER TABLE webhook_configs DROP CONSTRAINT IF EXISTS webhook_configs_workspace_id_fkey CASCADE")
            op.drop_column("webhook_configs", "workspace_id")

    # Drop workspaces table
    if "workspaces" in existing_tables:
        op.drop_table("workspaces")


def downgrade() -> None:
    """Recreate workspaces table if needed."""
    op.create_table(
        "workspaces",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("storage_mask", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
