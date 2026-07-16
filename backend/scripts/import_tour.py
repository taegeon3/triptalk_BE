
from __future__ import annotations

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.database import SessionLocal, init_db
from app.crud import create_tour_spot


DATA_DIR = BASE_DIR / "data"


def load_json_files() -> list[Path]:
    return sorted(DATA_DIR.glob("*.json"))


def import_tour_data() -> int:
    init_db()

    json_files = load_json_files()
    if not json_files:
        print("No JSON files found in data folder")
        return 0

    imported_count = 0

    for json_path in json_files:
        with json_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        content_type_id = int(data.get("contentTypeId", 0))
        items = data.get("items", [])

        with SessionLocal() as db:
            for item in items:
                content_id = str(item.get("contentid", "")).strip()
                if not content_id:
                    continue

                title = item.get("title") or ""
                address = item.get("addr1") or ""
                overview = item.get("overview") or item.get("addr1") or ""
                latitude = None
                longitude = None
                area_code = None
                sigungu_code = None

                try:
                    latitude = float(item.get("mapy")) if item.get("mapy") not in (None, "") else None
                    longitude = float(item.get("mapx")) if item.get("mapx") not in (None, "") else None
                except (TypeError, ValueError):
                    latitude = None
                    longitude = None

                try:
                    area_code = int(str(item.get("areacode", "")).strip()) if str(item.get("areacode", "")).strip() else None
                except (TypeError, ValueError):
                    area_code = None

                try:
                    sigungu_code = int(str(item.get("sigungucode", "")).strip()) if str(item.get("sigungucode", "")).strip() else None
                except (TypeError, ValueError):
                    sigungu_code = None

                created = create_tour_spot(
                    db,
                    content_id=content_id,
                    content_type_id=content_type_id,
                    title=title,
                    address=address,
                    overview=overview,
                    latitude=latitude,
                    longitude=longitude,
                    area_code=area_code,
                    sigungu_code=sigungu_code,
                )
                if created is not None:
                    imported_count += 1

    print(f"Imported {imported_count} tour spots")
    return imported_count


if __name__ == "__main__":
    import_tour_data()
