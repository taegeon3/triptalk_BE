from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from app.database import Base


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    content_type_id = Column(Integer, nullable=False, index=True)
    title = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    password_hash = Column(String(255), nullable=False)
    like_count = Column(Integer, default=0, nullable=False)
    view_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class TourSpot(Base):
    __tablename__ = "tour_spots"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(String(50), unique=True, index=True, nullable=False)
    content_type_id = Column(Integer, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    address = Column(String(255), nullable=True)
    overview = Column(Text, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    area_code = Column(Integer, nullable=True, index=True)
    sigungu_code = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)