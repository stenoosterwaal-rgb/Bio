import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "bio_tracker.db"
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
