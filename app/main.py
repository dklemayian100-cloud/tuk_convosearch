"""
TUK-ConvoSearch — FastAPI entry point.

Wires the API routers together and exposes the ASGI app for uvicorn.
Location: app/main.py
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat_proposal import router as chat_router


app = FastAPI(
    title="TUK-ConvoSearch",
    description="Modular RAG framework — question answering over your own documents.",
    version="0.1.0",
)

# Allow the local frontend (Vite dev server, static HTML, etc.) to call the API.
# In production, replace "*" with the actual frontend origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)


@app.get("/")
def root():
    return {
        "service": "TUK-ConvoSearch",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }