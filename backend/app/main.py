from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")

from app.database import init_db
from app.routers import locations, posts
from app.routers.chat import router as chat_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="TripTalk API", lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://triptalk-fe.netlify.app/",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(posts.router, prefix="/posts", tags=["posts"])
app.include_router(locations.router, prefix="/locations", tags=["locations"])
app.include_router(chat_router, prefix="/api", tags=["chat"])


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}