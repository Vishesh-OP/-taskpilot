from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import Base, engine
from .routers import admin, auth, chat, tasks

app = FastAPI(title="TaskPilot API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=settings.origins, allow_methods=["*"], allow_headers=["*"])

Base.metadata.create_all(engine)

for r in (auth.router, tasks.router, chat.router, admin.router):
    app.include_router(r)


@app.get("/", tags=["health"])
def health():
    return {"status": "ok", "docs": "/docs"}
