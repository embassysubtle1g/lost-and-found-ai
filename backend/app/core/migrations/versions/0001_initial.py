from alembic import op

revision = "0001"
down_revision = None

STATEMENTS = [
    "CREATE EXTENSION IF NOT EXISTS vector",
    """
    CREATE TABLE organizations (
        id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        name text NOT NULL UNIQUE,
        address text NOT NULL,
        phone text NOT NULL
    )
    """,
    """
    CREATE TABLE staff_accounts (
        id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        organization_id bigint NOT NULL REFERENCES organizations(id),
        username text NOT NULL UNIQUE,
        password_hash text NOT NULL,
        enabled boolean NOT NULL DEFAULT true
    )
    """,
    """
    CREATE TABLE sessions (
        token_hash text PRIMARY KEY,
        staff_id bigint NOT NULL REFERENCES staff_accounts(id) ON DELETE CASCADE,
        expires_at timestamptz NOT NULL,
        revoked_at timestamptz
    )
    """,
    "CREATE INDEX sessions_staff_idx ON sessions(staff_id)",
    """
    CREATE TABLE items (
        id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        reference text NOT NULL UNIQUE,
        organization_id bigint NOT NULL REFERENCES organizations(id),
        name text NOT NULL,
        category text NOT NULL,
        found_date date NOT NULL,
        found_location text NOT NULL,
        private_note text NOT NULL DEFAULT '',
        status text NOT NULL DEFAULT 'AVAILABLE'
            CHECK (status IN ('AVAILABLE', 'RETURNED', 'WITHDRAWN')),
        returned_at timestamptz,
        returned_by bigint REFERENCES staff_accounts(id),
        CHECK (
            (status = 'RETURNED' AND returned_at IS NOT NULL AND returned_by IS NOT NULL)
            OR (status <> 'RETURNED' AND returned_at IS NULL AND returned_by IS NULL)
        )
    )
    """,
    "CREATE INDEX items_org_idx ON items(organization_id, id DESC)",
    "CREATE INDEX items_public_idx ON items(id DESC) WHERE status = 'AVAILABLE'",
    """
    CREATE TABLE item_images (
        id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        item_id bigint NOT NULL REFERENCES items(id),
        object_key text NOT NULL UNIQUE,
        media_type text NOT NULL,
        size_bytes integer NOT NULL CHECK (size_bytes > 0),
        is_cover boolean NOT NULL DEFAULT false,
        state text NOT NULL DEFAULT 'PENDING'
            CHECK (state IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')),
        error text,
        model text,
        model_version text,
        embedding vector(768),
        removed_at timestamptz,
        CHECK (state <> 'COMPLETED' OR
               (embedding IS NOT NULL AND model IS NOT NULL AND model_version IS NOT NULL))
    )
    """,
    "CREATE UNIQUE INDEX image_cover_idx ON item_images(item_id) WHERE is_cover AND removed_at IS NULL",
    "CREATE INDEX image_item_idx ON item_images(item_id) WHERE removed_at IS NULL",
    "CREATE INDEX image_work_idx ON item_images(id) WHERE state = 'PENDING' OR removed_at IS NOT NULL",
]


def upgrade():
    for statement in STATEMENTS:
        op.execute(statement)


def downgrade():
    op.execute("DROP TABLE item_images, items, sessions, staff_accounts, organizations")
