from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import PlainTextResponse
from openai import OpenAI
from pydantic import BaseModel, Field

router = APIRouter()

BACKEND_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BACKEND_DIR / "data"
MAX_CONTEXT_ITEMS = 20
CATEGORY_KEYWORDS = {
    "12": ("관광지", "명소", "가볼만한 곳", "가볼 곳"),
    "14": ("문화시설", "문화 시설", "박물관", "미술관"),
    "15": ("축제", "공연", "행사"),
    "25": ("여행코스", "여행 코스", "코스"),
    "28": ("레포츠", "스포츠", "체험", "액티비티"),
    "32": ("숙박", "숙소", "호텔", "펜션"),
    "38": ("쇼핑", "시장", "기념품"),
    "39": ("맛집", "음식점", "식당", "먹을 곳", "밥집", "카페"),
}


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)


@lru_cache(maxsize=1)
def load_tour_data() -> tuple[dict[str, Any], ...]:
    items: list[dict[str, Any]] = []
    for json_path in sorted(DATA_DIR.glob("*.json")):
        with json_path.open("r", encoding="utf-8") as file:
            payload = json.load(file)

        if isinstance(payload, dict) and isinstance(payload.get("items"), list):
            content_type_id = str(payload.get("contentTypeId", ""))
            for item in payload["items"]:
                if isinstance(item, dict):
                    copied = dict(item)
                    copied.setdefault("contenttypeid", content_type_id)
                    items.append(copied)
        elif isinstance(payload, list):
            items.extend(item for item in payload if isinstance(item, dict))
    return tuple(items)


def normalize(text: str) -> str:
    lowered = str(text).lower()
    return re.sub(r"[^0-9a-z가-힣]+", " ", lowered).strip()


def infer_content_type(question: str) -> str | None:
    normalized_question = normalize(question)
    for content_type_id, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in normalized_question for keyword in keywords):
            return content_type_id
    return None


def question_tokens(question: str) -> set[str]:
    particles = ("에서", "으로", "에게", "한테", "에는", "에", "은", "는", "이", "가", "을", "를", "도")
    tokens: set[str] = set()
    for token in normalize(question).split():
        if len(token) < 2:
            continue
        tokens.add(token)
        for particle in particles:
            if token.endswith(particle) and len(token) > len(particle) + 1:
                tokens.add(token[: -len(particle)])
                break
    return tokens


def search_items(question: str, items: tuple[dict[str, Any], ...]) -> list[dict[str, Any]]:
    normalized_question = normalize(question)
    tokens = question_tokens(question)
    requested_content_type = infer_content_type(question)
    scored: list[tuple[int, str, dict[str, Any]]] = []

    for item in items:
        item_content_type = str(item.get("contenttypeid", ""))
        if requested_content_type and item_content_type != requested_content_type:
            continue

        title = normalize(item.get("title", ""))
        address = normalize(f'{item.get("addr1", "")} {item.get("addr2", "")}')
        overview = normalize(item.get("overview", ""))
        score = 0

        if title and title in normalized_question:
            score += 20
        for token in tokens:
            if token in title:
                score += 6
            elif token in address:
                score += 4
            elif token in overview:
                score += 2

        if score > 0:
            scored.append((score, title, item))

    scored.sort(key=lambda value: (-value[0], value[1]))
    if scored:
        return [item for _, _, item in scored[:MAX_CONTEXT_ITEMS]]

    # 검색어가 너무 일반적인 경우에도 임의의 한 곳을 사실처럼 추천하지 않도록
    # 소량의 데이터만 제공하고 모델이 질문을 구체화하도록 유도한다.
    return list(items[:5])


def compact_item(item: dict[str, Any]) -> dict[str, Any]:
    fields = (
        "contentid",
        "contenttypeid",
        "title",
        "addr1",
        "addr2",
        "tel",
        "mapx",
        "mapy",
        "firstimage",
        "overview",
    )
    return {field: item[field] for field in fields if item.get(field) not in (None, "")}


@router.post("/chat", response_class=PlainTextResponse)
def chat(payload: ChatRequest) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OPENAI_API_KEY가 설정되지 않았습니다.",
        )

    items = load_tour_data()
    if not items:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="지역 JSON 데이터가 없습니다.",
        )

    candidates = search_items(payload.question, items)
    context = json.dumps(
        [compact_item(item) for item in candidates],
        ensure_ascii=False,
        separators=(",", ":"),
    )

    try:
        response = OpenAI(api_key=api_key).responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            instructions=(
                "당신은 TripTalk의 한국 여행 정보 안내 챗봇입니다. "
                "반드시 제공된 JSON 데이터에 있는 사실만 사용해 한국어로 자연스럽게 답하세요. "
                "데이터에 없는 운영시간, 가격, 평가, 교통편 등은 추측하지 마세요. "
                "질문에 답할 근거가 부족하면 정보가 부족하다고 말하고 지역이나 장소를 더 구체적으로 물어보세요. "
                "추천 요청에는 가능한 경우 장소명과 주소를 함께 알려주세요."
            ),
            input=f"사용자 질문:\n{payload.question}\n\n검색된 지역 JSON 데이터:\n{context}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OpenAI 응답 생성에 실패했습니다: {exc}",
        ) from exc

    answer = response.output_text.strip()
    if not answer:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="OpenAI 응답이 비어 있습니다.",
        )

    return answer
