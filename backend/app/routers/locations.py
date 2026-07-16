from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.crud import get_tour_spot_by_content_id, list_tour_spots
from app.database import get_db
from app.schemas import (
    ErrorResponse,
    LocationDetailResponse,
    LocationListItem,
    LocationListResponse,
)

router = APIRouter()


@router.get(
    "/",
    response_model=LocationListResponse,
    responses={404: {"model": ErrorResponse}},
)
def read_locations(
    contentTypeId: Optional[int] = Query(default=None),
    areaCode: Optional[int] = Query(default=None),
    sigunguCode: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
):
    spots = list_tour_spots(
        db,
        content_type_id=contentTypeId,
        area_code=areaCode,
        sigungu_code=sigunguCode,
    )

    items = [
        LocationListItem(
            contentId=spot.content_id,
            title=spot.title,
            addr1=spot.address or "",
            addr2="",
            mapx=float(spot.longitude) if spot.longitude is not None else 0.0,
            mapy=float(spot.latitude) if spot.latitude is not None else 0.0,
            mlevel=6,
            firstimage="",
            firstimage2="",
            tel="",
        )
        for spot in spots
    ]

    return LocationListResponse(locations=items)


@router.get(
    "/content/{content_id}",
    response_model=LocationDetailResponse,
    responses={404: {"model": ErrorResponse}},
)
def read_location_detail(content_id: str, db: Session = Depends(get_db)):
    spot = get_tour_spot_by_content_id(db, content_id)
    if not spot:
        raise HTTPException(status_code=404, detail={"message": "위치 정보를 찾을 수 없습니다.", "errorCode": "LOCATION_NOT_FOUND"})

    return LocationDetailResponse(
        contentId=spot.content_id,
        addr1=spot.address or "",
        addr2="",
        areacode="",
        cat1="",
        cat2="",
        cat3="",
        contenttypeid=str(spot.content_type_id),
        createdtime="",
        firstimage="",
        firstimage2="",
        cpyrhtDivCd="",
        mapx=float(spot.longitude) if spot.longitude is not None else 0.0,
        mapy=float(spot.latitude) if spot.latitude is not None else 0.0,
        mlevel="6",
        modifiedtime="",
        sigungucode="",
        tel="",
        title=spot.title,
        zipcode="",
        IDongRegnCd="",
        IDongSigunguCd="",
        lclsSystm1="",
        lclsSystm2="",
        lclsSystm3="",
    )
