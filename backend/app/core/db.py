import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

engine = create_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)


def query(connection, sql, **parameters):
    return connection.execute(text(sql), parameters)


def one(connection, sql, **parameters):
    return query(connection, sql, **parameters).mappings().first()


def rows(connection, sql, **parameters):
    return [dict(row) for row in query(connection, sql, **parameters).mappings()]
