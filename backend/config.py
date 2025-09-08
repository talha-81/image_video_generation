import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Directory configuration
BASE_DIR = Path(__file__).resolve().parent
PROJECTS_DIR = BASE_DIR / "image_generation"
PROJECTS_DIR.mkdir(exist_ok=True)

# API Configuration
CONFIG = {
    "runware": {
        "api_key": os.getenv("RUNWARE_API_KEY", "your_key_here"),
        "api_url": "https://api.runware.ai/v1/imageInference",
        "models": [
            "runware:101@1",
            "runware:102@1",
            "runware:103@1"
        ]
    },
    "together": {
        "api_key": os.getenv("TOGETHER_API_KEY", "your_key_here"),
        "api_url": "https://api.together.xyz/v1/images/generations",
        "models": [
            "black-forest-labs/FLUX.1-schnell",
            "black-forest-labs/FLUX.1-schnell-Free",
            "black-forest-labs/FLUX.1-standard-Pro"
        ]
    },
    "openrouter": {
        "api_key": os.getenv("OPENAI_API_KEY", "your_key_here"),
        "api_url": "https://api.openai.com/v1/chat/completions",
        "models": [
            "gpt-4o-mini",
            "gpt-4.1-mini"
        ]
    }

}

# Runtime configuration
TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "60"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", "2"))
