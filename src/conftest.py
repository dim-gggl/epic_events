import os
import sys


# Ensure SECRET_KEY for tests that rely on it
os.environ.setdefault("SECRET_KEY", "test-secret")

# Make repository root importable so `import src...` works
CURRENT_DIR = os.path.dirname(__file__)
REPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


