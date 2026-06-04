import os
import sys
import traceback
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

# Vercel deploys the contents of the 'backend' folder as the root.
# This creates a symlink to make the backend folder importable as a 'backend' package.
tmp_dir = "/tmp/vercel_backend_pkg"
os.makedirs(tmp_dir, exist_ok=True)
symlink_path = os.path.join(tmp_dir, "backend")

if not os.path.exists(symlink_path):
    try:
        os.symlink(os.getcwd(), symlink_path, target_is_directory=True)
    except Exception:
        pass

# Inject the package directory into Python's search path
if tmp_dir not in sys.path:
    sys.path.insert(0, tmp_dir)

# Initialize app variable
app = None

try:
    # Import the main FastAPI app from the backend package context
    from backend.main import app as _app
    app = _app
except Exception as e:
    # Capture error details into variables that can be accessed by the fallback_route
    error_message = str(e)
    error_traceback = traceback.format_exc()
    
    # Print to Vercel logs for server-side debugging
    print("CRITICAL: Failed to import backend.main", file=sys.stderr)
    print(error_traceback, file=sys.stderr)
    
    fallback_app = FastAPI(title="Backend Load Error")
    
    def html_escape(text: str) -> str:
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#x27;")
    
    @fallback_app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"])
    async def fallback_route(path: str):
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Backend Initialization Error</title>
            <style>
                body {{ font-family: -apple-system, sans-serif; background-color: #f7fafc; color: #2d3748; padding: 40px; line-height: 1.6; }}
                .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; }}
                h1 {{ color: #e53e3e; font-size: 24px; border-bottom: 2px solid #fed7d7; padding-bottom: 10px; }}
                pre {{ background: #1a202c; color: #edf2f7; padding: 15px; border-radius: 8px; overflow-x: auto; font-size: 13px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>⚠️ Backend Initialization Failed</h1>
                <p>An exception occurred while importing the backend application.</p>
                <h3>Error Details:</h3>
                <pre>{html_escape(error_message)}</pre>
                <h3>Traceback:</h3>
                <pre>{html_escape(error_traceback)}</pre>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content, status_code=500)
    
    app = fallback_app