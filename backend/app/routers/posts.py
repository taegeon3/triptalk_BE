from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.crud import (
    create_post,
    delete_post,
    get_post_by_id,
    like_post,
    list_posts,
    update_post,
)
from app.database import get_db
from app.schemas import (
    ErrorResponse,
    PostCreateRequest,
    PostCreateResponse,
    PostDetailResponse,
    PostLikeResponse,
    PostListItem,
    PostListResponse,
    PostUpdateRequest,
    PostVerifyPasswordRequest,
    PostVerifyPasswordResponse,
)

router = APIRouter()


def _hash_password(password: str) -> str:
    return password


@router.get(
    "/",
    response_model=PostListResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def read_posts(
    keyword: Optional[str] = Query(default=None),
    sort: str = Query(default="latest"),
    contentTypeId: Optional[int] = Query(default=None),
    cursor: Optional[int] = Query(default=None),
    size: int = Query(default=10),
    db: Session = Depends(get_db),
):
    posts, next_cursor = list_posts(
        db,
        keyword=keyword,
        content_type_id=contentTypeId,
        sort=sort,
        cursor=cursor,
        size=size,
    )

    response_posts = [
        PostListItem(
            postId=post.id,
            contentTypeId=post.content_type_id,
            title=post.title,
            content=post.content,
            likeCount=post.like_count,
            createdAt=post.created_at.isoformat(),
            viewCount=post.view_count,
        )
        for post in posts
    ]

    return PostListResponse(
        posts=response_posts,
        nextCursor=next_cursor,
        message="게시글 목록 조회 성공",
    )


@router.get(
    "/{post_id}",
    response_model=PostDetailResponse,
    responses={404: {"model": ErrorResponse}},
)
def read_post(post_id: int, db: Session = Depends(get_db)):
    post = get_post_by_id(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail={"message": "게시글을 찾을 수 없습니다.", "errorCode": "POST_NOT_FOUND"})

    return PostDetailResponse(
        postId=post.id,
        contentTypeId=post.content_type_id,
        title=post.title,
        content=post.content,
        likeCount=post.like_count,
        viewCount=post.view_count,
        createdAt=post.created_at.isoformat(),
    )


@router.post("/", response_model=PostCreateResponse, status_code=status.HTTP_201_CREATED)
def create_post_endpoint(
    request: PostCreateRequest,
    db: Session = Depends(get_db),
):
    if request.contentTypeId not in {12, 14, 15, 25, 28, 32, 38, 39}:
        raise HTTPException(status_code=400, detail={"message": "지원하지 않는 contentTypeId입니다.", "errorCode": "INVALID_CONTENT_TYPE_ID"})

    post = create_post(
        db,
        title=request.title,
        content=request.content,
        password_hash=_hash_password(request.password),
        content_type_id=request.contentTypeId,
    )

    return PostCreateResponse(postId=post.id, message="게시글 생성 성공")


@router.post(
    "/{post_id}/verify-password",
    response_model=PostVerifyPasswordResponse,
    responses={404: {"model": ErrorResponse}},
)
def verify_password(post_id: int, request: PostVerifyPasswordRequest, db: Session = Depends(get_db)):
    post = get_post_by_id(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail={"message": "게시글을 찾을 수 없습니다.", "errorCode": "POST_NOT_FOUND"})

    verified = _hash_password(request.password) == post.password_hash
    if not verified:
        raise HTTPException(status_code=401, detail={"message": "비밀번호가 일치하지 않습니다.", "errorCode": "INVALID_PASSWORD"})

    return PostVerifyPasswordResponse(verified=True, message="비밀번호 검증 성공")


@router.put("/{post_id}", response_model=dict)
def update_post_endpoint(post_id: int, request: PostUpdateRequest, db: Session = Depends(get_db)):
    post = get_post_by_id(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail={"message": "게시글을 찾을 수 없습니다.", "errorCode": "POST_NOT_FOUND"})

    update_post(db, post, title=request.title, content=request.content)
    return {"message": "게시글 수정 성공"}


@router.delete("/{post_id}", response_model=dict)
def delete_post_endpoint(post_id: int, db: Session = Depends(get_db)):
    post = get_post_by_id(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail={"message": "게시글을 찾을 수 없습니다.", "errorCode": "POST_NOT_FOUND"})

    delete_post(db, post)
    return {"message": "게시글 삭제 성공"}


@router.post("/{post_id}/likes", response_model=PostLikeResponse)
def like_post_endpoint(
    post_id: int,
    db: Session = Depends(get_db)
):
    print("좋아요 API 호출됨:", post_id)

    post = get_post_by_id(db, post_id)

    if not post:
        print("게시글 없음:", post_id)
        raise HTTPException(
            status_code=404,
            detail={
                "message": "게시글을 찾을 수 없습니다.",
                "errorCode": "POST_NOT_FOUND"
            }
        )

    print("게시글 찾음:", post.id)

    like_post(db, post)

    return PostLikeResponse(
        postId=post.id,
        likeCount=post.like_count,
        message="좋아요 반영 성공"
    )