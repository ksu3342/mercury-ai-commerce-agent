from fastapi import FastAPI

from app.api import router


app = FastAPI(
    title="Mercury AI Commerce Agent Backend MVP",
    version="0.1.0",
    description="Portfolio PoC backend for the Mercury demo workflow.",
)
app.include_router(router)
