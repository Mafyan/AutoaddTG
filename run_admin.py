#!/usr/bin/env python3
"""Script to run the admin panel."""
import uvicorn
from config import settings

if __name__ == "__main__":
    print("="*60)
    print("Starting Admin Panel...")
    print(f"URL: http://{settings.ADMIN_PANEL_HOST}:{settings.ADMIN_PANEL_PORT}")
    print("="*60)
    
    uvicorn.run(
        "admin_panel.main:app",
        host=settings.ADMIN_PANEL_HOST,
        port=settings.ADMIN_PANEL_PORT,
        reload=False
    )

