#!/usr/bin/env python3
"""
Start the FastAPI backend server
"""

import sys
import os
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set environment
os.environ["PYTHONPATH"] = str(project_root)

# Import FastAPI and run server
import uvicorn
from app.backend.api.main import app

if __name__ == "__main__":
    print("="*70)
    print("Starting FastAPI Backend Server")
    print("="*70)
    print()
    print("Server will start at: http://localhost:5000")
    print()
    print("Press Ctrl+C to stop the server")
    print()
    print("="*70)
    print()

    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=5000,
            reload=False
        )
    except KeyboardInterrupt:
        print("\n\nServer stopped")
        sys.exit(0)
