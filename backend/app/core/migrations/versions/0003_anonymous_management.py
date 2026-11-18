from alembic import op

revision = "0003"
down_revision = "0002"


def upgrade():
    # Existing return history remains intact. New returns have no account actor.
    op.execute("""
        DO $$
        DECLARE existing_check record;
        BEGIN
            FOR existing_check IN
                SELECT conname FROM pg_constraint
                WHERE conrelid = 'items'::regclass AND contype = 'c'
                  AND pg_get_constraintdef(oid) LIKE '%returned_by%'
            LOOP
                EXECUTE format('ALTER TABLE items DROP CONSTRAINT %I', existing_check.conname);
            END LOOP;
        END $$
    """)
    op.execute("""
        ALTER TABLE items ADD CONSTRAINT items_return_state_check CHECK (
            (status = 'RETURNED' AND returned_at IS NOT NULL)
            OR (status <> 'RETURNED' AND returned_at IS NULL AND returned_by IS NULL)
        )
    """)


def downgrade():
    connection = op.get_bind()
    from sqlalchemy import text

    count = connection.execute(text(
        "SELECT count(*) FROM items WHERE status = 'RETURNED' AND returned_by IS NULL"
    )).scalar_one()
    if count:
        raise RuntimeError("存在免登入歸還紀錄，請保留 0003 以維持歷史資料。")
    op.execute("ALTER TABLE items DROP CONSTRAINT items_return_state_check")
    op.execute("""
        ALTER TABLE items ADD CONSTRAINT items_return_state_check CHECK (
            (status = 'RETURNED' AND returned_at IS NOT NULL AND returned_by IS NOT NULL)
            OR (status <> 'RETURNED' AND returned_at IS NULL AND returned_by IS NULL)
        )
    """)
