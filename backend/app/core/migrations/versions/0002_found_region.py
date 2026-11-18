from alembic import op

revision = "0002"
down_revision = "0001"


def upgrade():
    op.execute("ALTER TABLE items ADD COLUMN found_region text NOT NULL DEFAULT ''")


def downgrade():
    op.execute("ALTER TABLE items DROP COLUMN found_region")
