from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import draft

app = FastAPI(title="Fantasy Football Draft Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(draft.router)


@app.get("/health")
def health():
    return {"status": "ok"}
