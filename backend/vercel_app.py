import os
import sys
import traceback

# Vercel deploys the contents of the 'backend' folder as the root.
# However, this project is designed as a package ('backend') with package-relative imports.
# To keep package-relative imports working seamlessly on Vercel, we dynamically
# create a symlink to make the backend folder importable as a 'backend' package.

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

# Initialize app variable at the top-level outer scope for Vercel's static analysis
app = None

try:
    # Import the main FastAPI app from the backend package context
    from backend.main import app as _app
    app = _app
except Exception as e:
    # If importing fails, construct a fallback FastAPI app to display the error beautifully in the browser.
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse
    
    # Print the error to stderr so it shows up in Vercel function logs
    print("CRITICAL: Failed to import backend.main", file=sys.stderr)
    traceback.print_exc()
    
    fallback_app = FastAPI(title="Backend Load Error")
    error_traceback = traceback.format_exc()
    
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
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                    background-color: #f7fafc;
                    color: #2d3748;
                    padding: 40px 20px;
                    line-height: 1.6;
                }}
                .container {{
                    max-width: 800px;
                    margin: 0 auto;
                    background: white;
                    padding: 30px;
                    border-radius: 12px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05), 0 1px 3px rgba(0, 0, 0, 0.1);
                    border: 1px solid #e2e8f0;
                }}
                h1 {{
                    color: #e53e3e;
                    margin-top: 0;
                    font-size: 24px;
                    border-bottom: 2px solid #fed7d7;
                    padding-bottom: 12px;
                }}
                p {{
                    font-size: 16px;
                }}
                pre {{
                    background: #1a202c;
                    color: #edf2f7;
                    padding: 16px;
                    border-radius: 8px;
                    overflow-x: auto;
                    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, Courier, monospace;
                    font-size: 14px;
                }}
                .tip {{
                    background-color: #ebf8ff;
                    border-left: 4px solid #3182ce;
                    color: #2b6cb0;
                    padding: 12px 16px;
                    border-radius: 0 8px 8px 0;
                    margin-top: 20px;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>⚠️ Backend Initialization Failed</h1>
                <p>An exception occurred while importing and setting up the backend application. This is typically due to missing environment variables on Vercel or database configuration issues.</p>
                
                <h3>Error Details:</h3>
                <pre>{html_escape(str(e))}</pre>
                
                <h3>Traceback:</h3>
                <pre>{html_escape(error_traceback)}</pre>
                
                <div class="tip">
                    <strong>💡 Troubleshooting Tip:</strong> Ensure that you have configured all required environment variables in your Vercel Project Dashboard (under <strong>Settings &gt; Environment Variables</strong>). You can copy the values from your local <code>.env</code> file.
                </div>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content, status_code=500)

    app = fallback_app
