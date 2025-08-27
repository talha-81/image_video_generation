import pytest
import os
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

# Set test environment variables before importing the app
os.environ.setdefault("OPENROUTER_API_KEY", "test_openrouter_key")
os.environ.setdefault("RUNWARE_API_KEY", "test_runware_key")
os.environ.setdefault("TOGETHER_API_KEY", "test_together_key")
os.environ.setdefault("HTTP_TIMEOUT", "30")
os.environ.setdefault("MAX_RETRIES", "2")
os.environ.setdefault("RETRY_DELAY", "1")

from backend.main import app
from backend.models.schemas import ScriptAnalysis, ScenePrompt, PreviewImage
from backend.models.session_manager import _sessions


@pytest.fixture(scope="session")
def client():
    """FastAPI test client fixture."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def clear_sessions():
    """Clear session registry before each test."""
    _sessions.clear()
    yield
    _sessions.clear()


@pytest.fixture
def temp_projects_dir():
    """Create temporary projects directory for testing."""
    temp_dir = tempfile.mkdtemp()
    
    # Patch all references to PROJECTS_DIR
    with patch("backend.config.PROJECTS_DIR", Path(temp_dir)), \
         patch("backend.main.PROJECTS_DIR", Path(temp_dir)), \
         patch("backend.utils.storage.PROJECTS_DIR", Path(temp_dir)), \
         patch("backend.utils.script_analysis.PROJECTS_DIR", Path(temp_dir)):
        yield Path(temp_dir)
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_script():
    """Sample script for testing."""
    return """Once upon a time, in a magical forest, there lived a brave young fox named Ruby. 
    She had bright red fur that gleamed in the sunlight and emerald green eyes that 
    sparkled with curiosity. Every morning, Ruby would venture out to explore the 
    mysterious paths that wound through the ancient trees.

    One day, while following a particularly intriguing trail, Ruby discovered a hidden 
    clearing where golden butterflies danced around a crystal clear pond."""


@pytest.fixture
def sample_analysis():
    """Sample script analysis."""
    return ScriptAnalysis(
        word_count=65,
        recommended_scenes=4,
        estimated_duration_minutes=0.3,
        complexity_score="Simple"
    )


@pytest.fixture
def mock_openrouter_success():
    """Mock successful OpenRouter API response."""
    mock_response = {
        "choices": [{
            "message": {
                "content": json.dumps({
                    "scenes": [
                        {
                            "scene_number": 1,
                            "scene_title": "Ruby in the Forest",
                            "script_excerpt": "Once upon a time, in a magical forest...",
                            "image_prompt": "Cinematic shot of a young fox with bright red fur in a magical forest"
                        },
                        {
                            "scene_number": 2,
                            "scene_title": "The Hidden Clearing",
                            "script_excerpt": "Ruby discovered a hidden clearing...",
                            "image_prompt": "Magical clearing with golden butterflies around a crystal pond"
                        }
                    ]
                })
            }
        }]
    }
    
    with patch("requests.post") as mock_post:
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_response
        mock_resp.raise_for_status.return_value = None
        mock_post.return_value = mock_resp
        yield mock_post


@pytest.fixture
def mock_image_generation_success():
    """Mock successful image generation."""
    def mock_runware_response(*args, **kwargs):
        return [{
            "taskUUID": "test-uuid",
            "imageURL": "https://example.com/test_image.jpg",
            "status": "success"
        }]
    
    def mock_together_response(*args, **kwargs):
        return {
            "data": [{
                "url": "https://example.com/test_image.jpg"
            }]
        }
    
    with patch("requests.post") as mock_post:
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status.return_value = None
        
        # Return different responses based on URL
        def side_effect(*args, **kwargs):
            url = args[0] if args else kwargs.get('url', '')
            if 'runware' in url:
                mock_resp.json.return_value = mock_runware_response()
            elif 'together' in url:
                mock_resp.json.return_value = mock_together_response()
            return mock_resp
        
        mock_post.side_effect = side_effect
        yield mock_post


@pytest.fixture
def mock_image_download():
    """Mock image download for saving approved images."""
    with patch("requests.get") as mock_get:
        mock_resp = Mock()
        mock_resp.content = b"fake_image_data"
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp
        yield mock_get


@pytest.fixture
def created_project(temp_projects_dir, sample_script, sample_analysis):
    """Create a test project in the temporary directory."""
    project_id = "test_project_123"
    project_path = temp_projects_dir / project_id
    project_path.mkdir(parents=True, exist_ok=True)
    (project_path / "images").mkdir(exist_ok=True)
    
    # Save script and analysis
    (project_path / "script.txt").write_text(sample_script, encoding="utf-8")
    (project_path / "analysis.json").write_text(
        json.dumps(sample_analysis.dict(), indent=2), 
        encoding="utf-8"
    )
    
    return project_id, project_path


# Utility functions for tests
def wait_for_generation_completion(client, session_id, max_attempts=10):
    """Wait for image generation to complete."""
    import time
    for _ in range(max_attempts):
        response = client.get(f"/generation-status/{session_id}")
        if response.status_code == 200:
            data = response.json()
            if data["status"] in ["previewing", "completed", "failed"]:
                return data
        time.sleep(0.5)
    return None