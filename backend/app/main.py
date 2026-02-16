"""FastAPI application entry point (per §10).

Mounts all API routers and configures CORS for the frontend.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, portfolio, reports, agents, chat, settings, websocket

app = FastAPI(
    title="Superhuman Alpha Fund",
    description="Multi-agent investment analysis system API",
    version="0.1.0",
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(auth.router)
app.include_router(portfolio.router)
app.include_router(reports.router)
app.include_router(agents.router)
app.include_router(chat.router)
app.include_router(settings.router)
app.include_router(websocket.router)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "superhuman-alpha-fund"}
