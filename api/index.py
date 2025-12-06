"""
Vercel Serverless Function Entry Point

This file is required by Vercel to serve the FastAPI application as a serverless function.
It imports the FastAPI app instance from app.main and exports it for Vercel to handle.
"""

from app.main import app

# Vercel will use this as the handler
handler = app
