from __future__ import annotations

import os
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "triptalk.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app.models import Post, TourSpot

    Base.metadata.create_all(bind=engine)

    with engine.begin() as conn:
        table_names = set(conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'" )).fetchall())
        if "tour_spots" in {name[0] for name in table_names}:
            existing_columns = set(conn.execute(text("PRAGMA table_info(tour_spots)")).fetchall())
            column_names = {row[1] for row in existing_columns}
            if "area_code" not in column_names:
                conn.execute(text("ALTER TABLE tour_spots ADD COLUMN area_code INTEGER"))
            if "sigungu_code" not in column_names:
                conn.execute(text("ALTER TABLE tour_spots ADD COLUMN sigungu_code INTEGER"))
