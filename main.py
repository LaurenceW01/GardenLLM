"""
Main entry point for GardenLLM web application.
This file provides a WSGI application that Render.com can use by default.
"""

from web import app

# WSGI application entry point
application = app

if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000))) 