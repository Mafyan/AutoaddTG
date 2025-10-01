"""Main FastAPI application for admin panel."""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from admin_panel.routes import router
from config import settings
import os

app = FastAPI(title="User Control Bot Admin Panel", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
if settings.STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(settings.STATIC_DIR)), name="static")

# Include router
app.include_router(router)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

