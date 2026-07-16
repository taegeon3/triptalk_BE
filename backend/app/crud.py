from __future__ import annotations

from typing import Optional, Sequence, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

AREA_CODE_MAP = {
    "광주광역시": 5,
    "전북특별자치도": 37,
    "전라남도": 38,
}

SIGUNGU_CODE_MAP = {
    5: {
        "동구": 1,
        "서구": 2,
        "남구": 3,
        "북구": 4,
        "광산구": 5,
    },
    37: {
        "전주시": 1,
        "군산시": 2,
        "익산시": 3,
        "정읍시": 4,
        "남원시": 5,
        "김제시": 6,
        "완주군": 7,
        "진안군": 8,
        "무주군": 9,
        "장수군": 10,
        "임실군": 11,
        "순창군": 12,
        "고창군": 13,
        "부안군": 14,
    },
    38: {
        "목포시": 1,
        "여수시": 2,
        "순천시": 3,
        "나주시": 4,
        "광양시": 5,
        "담양군": 6,
        "곡성군": 7,
        "구례군": 8,
        "고흥군": 9,
        "보성군": 10,
        "화순군": 11,
        "장흥군": 12,
        "강진군": 13,
        "해남군": 14,
        "영암군": 15,
        "무안군": 16,
        "함평군": 17,
        "영광군": 18,
        "장성군": 19,
        "완도군": 20,
        "진도군": 21,
        "신안군": 22,
    },
}


def _normalize_code(value: Optional[object], *, mapping: Optional[dict[object, int]] = None) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        if value.isdigit():
            return int(value)
        if mapping is not None:
            return mapping.get(value)
    return None


def _resolve_area_code(area_code: Optional[object]) -> Optional[int]:
    if isinstance(area_code, str):
        return _normalize_code(AREA_CODE_MAP.get(area_code), mapping=None)
    return _normalize_code(area_code, mapping=None)


def _resolve_sigungu_code(sigungu_code: Optional[object], area_code: Optional[object]) -> Optional[int]:
    area_code_value = _normalize_code(area_code, mapping=None)
    if area_code_value is None:
        return None

    if isinstance(sigungu_code, str):
        if sigungu_code.isdigit():
            return int(sigungu_code)
        return _normalize_code(sigungu_code, mapping={name: code for name, code in SIGUNGU_CODE_MAP.get(area_code_value, {}).items()})

    return _normalize_code(sigungu_code, mapping=None)

from app.models import Post, TourSpot


def create_post(
    db: Session,
    *,
    title: str,
    content: str,
    password_hash: str,
    content_type_id: int,
) -> Post:
    post = Post(
        title=title,
        content=content,
        password_hash=password_hash,
        content_type_id=content_type_id,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def get_post_by_id(db: Session, post_id: int) -> Optional[Post]:
    return db.get(Post, post_id)


def list_posts(
    db: Session,
    *,
    keyword: Optional[str] = None,
    content_type_id: Optional[int] = None,
    sort: str = "latest",
    cursor: Optional[int] = None,
    size: int = 10,
) -> Tuple[Sequence[Post], Optional[int]]:
    query = select(Post)

    if content_type_id is not None:
        query = query.where(Post.content_type_id == content_type_id)

    if keyword:
        like_keyword = f"%{keyword}%"
        query = query.where(
            or_(Post.title.like(like_keyword), Post.content.like(like_keyword))
        )

    if sort == "like":
        query = query.order_by(Post.like_count.desc(), Post.created_at.desc(), Post.id.desc())
    else:
        query = query.order_by(Post.created_at.desc(), Post.id.desc())

    if cursor is not None:
        query = query.where(Post.id < cursor)

    query = query.limit(size + 1)
    posts = db.scalars(query).all()

    next_cursor = posts[-1].id if len(posts) > size else None
    return posts[:size], next_cursor


def update_post(db: Session, post: Post, *, title: str, content: str) -> Post:
    post.title = title
    post.content = content
    db.commit()
    db.refresh(post)
    return post


def delete_post(db: Session, post: Post) -> None:
    db.delete(post)
    db.commit()


def like_post(db: Session, post: Post) -> Post:
    post.like_count += 1
    db.commit()
    db.refresh(post)
    return post


def create_tour_spot(
    db: Session,
    *,
    content_id: str,
    content_type_id: int,
    title: str,
    address: Optional[str] = None,
    overview: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    area_code: Optional[int] = None,
    sigungu_code: Optional[int] = None,
) -> Optional[TourSpot]:
    existing = get_tour_spot_by_content_id(db, content_id)
    if existing is not None:
        if area_code is not None:
            existing.area_code = area_code
        if sigungu_code is not None:
            existing.sigungu_code = sigungu_code
        db.commit()
        db.refresh(existing)
        return existing

    tour_spot = TourSpot(
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
    db.add(tour_spot)
    db.commit()
    db.refresh(tour_spot)
    return tour_spot


def list_tour_spots(
    db: Session,
    *,
    content_type_id: Optional[int] = None,
    area_code: Optional[object] = None,
    sigungu_code: Optional[object] = None,
) -> Sequence[TourSpot]:
    query = db.query(TourSpot)

    if content_type_id is not None:
        query = query.filter(TourSpot.content_type_id == content_type_id)

    resolved_area_code = _resolve_area_code(area_code)
    resolved_sigungu_code = _resolve_sigungu_code(sigungu_code, area_code)

    if resolved_area_code is not None:
        query = query.filter(TourSpot.area_code == resolved_area_code)

    if resolved_sigungu_code is not None:
        query = query.filter(TourSpot.sigungu_code == resolved_sigungu_code)

    return query.order_by(func.lower(TourSpot.title).asc(), TourSpot.title.asc(), TourSpot.id.asc()).all()


def get_tour_spot_by_content_id(db: Session, content_id: str) -> Optional[TourSpot]:
    return db.query(TourSpot).filter(TourSpot.content_id == content_id).first()
