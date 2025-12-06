"""
Vercel Serverless Function Entry Point

This file is required by Vercel to serve the FastAPI application as a serverless function.
"""

import sys
import os

# Add the root directory to Python path so imports work correctly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app

# Export the FastAPI app directly for Vercel
app = app
