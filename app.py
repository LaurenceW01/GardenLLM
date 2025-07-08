"""
WSGI entry point for GardenLLM web application.
This file provides a simple WSGI application that Render.com can use.
"""

from web import app
import os

# WSGI application entry point
application = app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000))) 