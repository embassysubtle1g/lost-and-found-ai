from .db import engine, one


def main():
    with engine.begin() as connection:
        for letter in ("A", "B"):
            one(connection, """
                INSERT INTO organizations(name, address, phone)
                VALUES (:name, :address, :phone)
                ON CONFLICT (name) DO NOTHING
                RETURNING id
            """, name=f"示範 {letter} 派出所", address=f"展示用地址 {letter}", phone="展示用電話")
    print("示範保管機構已就緒，可直接開啟物品管理頁。")


if __name__ == "__main__":
    main()
