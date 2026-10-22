import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.core.init_db import init_database
from app.api.auth import router as auth_router
from app.api.tickets import router as tickets_router
from app.api.knowledge_base import router as kb_router
from app.api.analytics import router as analytics_router
from app.api.copilot import router as copilot_router
from app.websockets.router import router as ws_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Omnichannel Live Support & Ticket Tracking API with AI Triage & Always-Connected WebSocket Sync"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(tickets_router, prefix=settings.API_V1_STR)
app.include_router(kb_router, prefix=settings.API_V1_STR)
app.include_router(analytics_router, prefix=settings.API_V1_STR)
app.include_router(copilot_router, prefix=settings.API_V1_STR)
app.include_router(ws_router)

# Mount Static Directories for Web Dashboard & Widget Demo
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
web_dashboard_path = os.path.join(BASE_DIR, "web-dashboard")
widget_path = os.path.join(BASE_DIR, "widget-js")

if os.path.exists(web_dashboard_path):
    app.mount("/dashboard", StaticFiles(directory=web_dashboard_path, html=True), name="dashboard")

if os.path.exists(widget_path):
    app.mount("/widget", StaticFiles(directory=widget_path, html=True), name="widget")

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
uploads_path = os.path.join(BACKEND_DIR, "uploads")
os.makedirs(uploads_path, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_path), name="uploads")

@app.on_event("startup")
def on_startup():
    init_database()

@app.get("/")
def root():
    return RedirectResponse(url="/dashboard/index.html")

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "CIHEUL Helpdesk Backend", "version": settings.VERSION}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
