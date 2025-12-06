"""
Vercel Serverless Function Entry Point

This file is required by Vercel to serve the FastAPI application as a serverless function.
"""

from mangum import Mangum
from app.main import app

# Mangum adapter for AWS Lambda/Vercel
handler = Mangum(app, lifespan="off")
