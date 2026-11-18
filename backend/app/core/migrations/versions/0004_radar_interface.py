from alembic import op

revision = "0004"
down_revision = "0003"


def upgrade():
    op.execute("ALTER TABLE items ADD COLUMN record_type text NOT NULL DEFAULT 'FOUND' CHECK (record_type IN ('LOST', 'FOUND'))")
    op.execute("ALTER TABLE items ADD COLUMN radar_data jsonb NOT NULL DEFAULT '{}'::jsonb")
    op.execute("""
        CREATE TABLE dismissed_matches (
            lost_id bigint NOT NULL REFERENCES items(id),
            found_id bigint NOT NULL REFERENCES items(id),
            PRIMARY KEY (lost_id, found_id)
        )
    """)


def downgrade():
    op.execute("DROP TABLE dismissed_matches")
    op.execute("ALTER TABLE items DROP COLUMN radar_data, DROP COLUMN record_type")
