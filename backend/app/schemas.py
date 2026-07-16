from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class PostCreateRequest(BaseModel):
    title: str
    content: str
    password: str
    contentTypeId: int


class PostUpdateRequest(BaseModel):
    title: str
    content: str


class PostVerifyPasswordRequest(BaseModel):
    password: str


class PostListItem(BaseModel):
    postId: int
    contentTypeId: int
    title: str
    content: str
    likeCount: int
    createdAt: str
    viewCount: int


class PostListResponse(BaseModel):
    posts: List[PostListItem]
    nextCursor: Optional[int]
    message: str


class PostDetailResponse(BaseModel):
    postId: int
    contentTypeId: int
    title: str
    content: str
    likeCount: int
    viewCount: int
    createdAt: str


class PostCreateResponse(BaseModel):
    postId: int
    message: str


class PostVerifyPasswordResponse(BaseModel):
    verified: bool
    message: str


class PostLikeResponse(BaseModel):
    postId: int
    likeCount: int
    message: str


class ErrorResponse(BaseModel):
    message: str
    errorCode: str


class LocationListItem(BaseModel):
    contentId: str
    title: str
    addr1: str
    addr2: str
    mapx: float
    mapy: float
    mlevel: int
    firstimage: str
    firstimage2: str
    tel: str


class LocationListResponse(BaseModel):
    locations: List[LocationListItem]


class LocationDetailResponse(BaseModel):
    contentId: str
    addr1: str
    addr2: str
    areacode: str
    cat1: str
    cat2: str
    cat3: str
    contenttypeid: str
    createdtime: str
    firstimage: str
    firstimage2: str
    cpyrhtDivCd: str
    mapx: float
    mapy: float
    mlevel: str
    modifiedtime: str
    sigungucode: str
    tel: str
    title: str
    zipcode: str
    IDongRegnCd: str
    IDongSigunguCd: str
    lclsSystm1: str
    lclsSystm2: str
    lclsSystm3: str
