import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed, assuming env vars are set manually
    pass

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# API settings
API_RESULT_LIMIT = 12

# UI / display settings
DISPLAY_BATCH_SIZE = 3

# Recipe filtering
MIN_MATCH_SCORE = 0.0

# Network settings
REQUEST_TIMEOUT = 8

# Metadata
USER_AGENT = "cooked-backend/1.0"
