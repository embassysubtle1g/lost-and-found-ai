import getpass

from app.db import engine, one, query
from app.security import password_hash


def main():
    accounts = []
    for suffix in ("a", "b"):
        username = f"station_{suffix}"
        password = getpass.getpass(f"{username} 的密碼（至少 10 字元）: ")
        if not 10 <= len(password) <= 160:
            raise SystemExit("密碼長度需為 10 到 160 字元")
        accounts.append((suffix, username, password_hash(password)))

    with engine.begin() as connection:
        for suffix, username, hashed in accounts:
            letter = suffix.upper()
            organization = one(connection, """
                INSERT INTO organizations(name, address, phone) VALUES (:name, :address, :phone)
                ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name RETURNING id
            """, name=f"示範 {letter} 派出所", address=f"展示用地址 {letter}", phone="展示用電話")
            query(connection, """
                INSERT INTO staff_accounts(organization_id, username, password_hash)
                VALUES (:org, :username, :password) ON CONFLICT (username) DO NOTHING
            """, org=organization.id, username=username, password=hashed)
    print("示範帳號 station_a、station_b 已就緒。既有帳號密碼維持原值。")


if __name__ == "__main__":
    main()
