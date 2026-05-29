import os
import sys

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

# Import the main FastAPI app from the backend package context
from backend.main import app
