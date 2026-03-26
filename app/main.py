from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers.chatbot import router as chatbot_router
from app.core.config import settings
from app.db.init_db import init_db

app = FastAPI(title="HDT AI Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chatbot_router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
