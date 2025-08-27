import pytest
import json
import requests
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from backend.utils.script_analysis import analyze_script, create_project
from backend.utils.prompt_generation import (
    generate_scene_prompts_openrouter, generate_fallback_scenes, 
    build_prompt, STYLE_MAP
)
from backend.utils.image_generation import (
    generate_image_runware, generate_image_together, generate_image_with_retry
)
from backend.utils.storage import (
    save_scene_prompts, save_approved_images, list_projects, get_project_details
)
from backend.models.schemas import ScenePrompt, PreviewImage, GenerationSession


class TestScriptAnalysisUtils:
    """Test script analysis utility functions."""
    
    def test_analyze_script_basic(self):
        """Test basic script analysis."""
        script = "The quick brown fox jumps over the lazy dog."
        analysis = analyze_script(script)
        
        assert analysis.word_count == 9
        assert analysis.recommended_scenes == 2  # < 100 words
        assert analysis.estimated_duration_minutes == 0.0  # 9/200 rounded to 0.0
        assert analysis.complexity_score == "Simple"  # Short words
    
    def test_analyze_script_word_count_ranges(self):
        """Test different word count ranges for scene recommendations."""
        test_cases = [
            (50, 2),    # < 100 words
            (150, 4),   # 100-300 words  
            (450, 6),   # 300-600 words
            (750, 9),   # 600-900 words
            (1200, 10), # > 900 words, capped at 10
        ]
        
        for word_count, expected_scenes in test_cases:
            script = " ".join(["word"] * word_count)
            analysis = analyze_script(script)
            assert analysis.word_count == word_count
            assert analysis.recommended_scenes == expected_scenes
    
    def test_analyze_script_complexity_scoring(self):
        """Test complexity score calculation."""
        # Simple words (average length <= 6)
        simple_script = "cat dog run jump play fun"
        simple_analysis = analyze_script(simple_script)
        assert simple_analysis.complexity_score == "Simple"
        
        # Complex words (average length > 6)
        complex_script = "magnificent extraordinary phenomenal"
        complex_analysis = analyze_script(complex_script)
        assert complex_analysis.complexity_score == "Complex"
    
    def test_analyze_empty_script(self):
        """Test analysis of empty script."""
        analysis = analyze_script("")
        assert analysis.word_count == 0
        assert analysis.recommended_scenes == 2
        assert analysis.estimated_duration_minutes == 0.0
        assert analysis.complexity_score == "Simple"  # Division by zero handled
    
    def test_create_project_structure(self, temp_projects_dir, sample_analysis):
        """Test project directory creation."""
        project_id = "test_project"
        script = "Test script content for project creation"
        
        with patch("backend.utils.script_analysis.PROJECTS_DIR", temp_projects_dir):
            project_path = create_project(project_id, script, sample_analysis)
        
        # Verify directory structure
        assert project_path.exists()
        assert project_path.is_dir()
        assert (project_path / "images").exists()
        assert (project_path / "images").is_dir()
        
        # Verify files
        script_file = project_path / "script.txt"
        analysis_file = project_path / "analysis.json"
        
        assert script_file.exists()
        assert analysis_file.exists()
        
        # Verify content
        assert script_file.read_text(encoding="utf-8") == script
        
        saved_analysis = json.loads(analysis_file.read_text(encoding="utf-8"))
        assert saved_analysis["word_count"] == sample_analysis.word_count
        assert saved_analysis["recommended_scenes"] == sample_analysis.recommended_scenes


class TestPromptGenerationUtils:
    """Test prompt generation utility functions."""
    
    def test_build_prompt_structure(self):
        """Test prompt building structure and content."""
        script = "A magical story about adventure"
        num_scenes = 3
        media_type = "cinematic"
        
        prompt = build_prompt(script, num_scenes, media_type)
        
        # Verify key components
        assert f"Create {num_scenes} detailed visual scene descriptions" in prompt
        assert script in prompt
        assert STYLE_MAP[media_type] in prompt
        assert "JSON" in prompt
        assert "scene_number" in prompt
        assert "scene_title" in prompt
        assert "script_excerpt" in prompt
        assert "image_prompt" in prompt
    
    def test_build_prompt_different_styles(self):
        """Test prompt building with different media types."""
        script = "Test script"
        
        for media_type, expected_style in STYLE_MAP.items():
            prompt = build_prompt(script, 2, media_type)
            assert expected_style in prompt
            assert f"in {expected_style}" in prompt
    
    def test_build_prompt_unknown_style(self):
        """Test prompt building with unknown media type."""
        script = "Test script"
        prompt = build_prompt(script, 2, "unknown_style")
        # Should default to cinematic
        assert "cinematic style" in prompt
    
    @patch("requests.post")
    def test_generate_scene_prompts_openrouter_success(self, mock_post):
        """Test successful OpenRouter scene generation."""
        # Mock successful response
        mock_response_data = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "scenes": [
                            {
                                "scene_number": 1,
                                "scene_title": "Opening Scene",
                                "script_excerpt": "Once upon a time...",
                                "image_prompt": "A magical forest with sunlight"
                            },
                            {
                                "scene_number": 2,
                                "scene_title": "Adventure Begins",
                                "script_excerpt": "The hero ventures forth...",
                                "image_prompt": "A brave adventurer on a path"
                            }
                        ]
                    })
                }
            }]
        }
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Test function
        script = "A test script for scene generation"
        scenes = generate_scene_prompts_openrouter(script, 2, "cinematic", "test-model")
        
        # Verify results
        assert len(scenes) == 2
        assert all(isinstance(scene, ScenePrompt) for scene in scenes)
        assert scenes[0].scene_number == 1
        assert scenes[0].scene_title == "Opening Scene"
        assert scenes[1].scene_number == 2
        assert scenes[1].scene_title == "Adventure Begins"
        
        # Verify API was called correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]["json"]["model"] == "test-model"
        assert script in call_args[1]["json"]["messages"][0]["content"]
    
    @patch("requests.post")
    def test_generate_scene_prompts_openrouter_json_with_markers(self, mock_post):
        """Test OpenRouter response with JSON code block markers."""
        json_content = {
            "scenes": [{
                "scene_number": 1,
                "scene_title": "Test Scene",
                "script_excerpt": "Test excerpt",
                "image_prompt": "Test prompt"
            }]
        }
        
        # Test with ```json markers
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": f"```json\n{json.dumps(json_content)}\n```"
                }
            }]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        scenes = generate_scene_prompts_openrouter("test", 1, "cinematic", "test-model")
        assert len(scenes) == 1
        assert scenes[0].scene_title == "Test Scene"
    
    @patch("requests.post")
    def test_generate_scene_prompts_openrouter_failure(self, mock_post):
        """Test OpenRouter failure fallback."""
        # Mock request exception
        mock_post.side_effect = requests.exceptions.RequestException("API Error")
        
        script = "Test script for failure scenario"
        scenes = generate_scene_prompts_openrouter(script, 2, "cinematic", "test-model")
        
        # Should fallback to generate_fallback_scenes
        assert len(scenes) == 2
        assert all(isinstance(scene, ScenePrompt) for scene in scenes)
        assert all("Scene" in scene.scene_title for scene in scenes)
    
    @patch("requests.post") 
    def test_generate_scene_prompts_openrouter_invalid_json(self, mock_post):
        """Test OpenRouter invalid JSON response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "invalid json response"
                }
            }]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        scenes = generate_scene_prompts_openrouter("test", 2, "cinematic", "test-model")
        
        # Should fallback
        assert len(scenes) == 2
        assert all(isinstance(scene, ScenePrompt) for scene in scenes)
    
    def test_generate_fallback_scenes(self):
        """Test fallback scene generation."""
        script = "This is a test script with multiple words for scene generation testing purposes."
        num_scenes = 3
        media_type = "cartoon"
        
        scenes = generate_fallback_scenes(script, num_scenes, media_type)
        
        assert len(scenes) == num_scenes
        assert all(isinstance(scene, ScenePrompt) for scene in scenes)
        
        # Verify scene structure
        for i, scene in enumerate(scenes):
            assert scene.scene_number == i + 1
            assert scene.scene_title == f"Scene {i + 1}"
            assert len(scene.script_excerpt) <= 100
            assert "Vibrant cartoon style scene" in scene.image_prompt
    
    def test_generate_fallback_scenes_empty_script(self):
        """Test fallback generation with empty script."""
        scenes = generate_fallback_scenes("", 2, "cinematic")
        
        assert len(scenes) == 2
        assert all(isinstance(scene, ScenePrompt) for scene in scenes)
        assert all(scene.script_excerpt == "" for scene in scenes)
    
    def test_generate_fallback_scenes_style_prefixes(self):
        """Test different style prefixes in fallback generation."""
        script = "Test script"
        
        style_tests = [
            ("cinematic", "Cinematic shot with dramatic lighting"),
            ("cartoon", "Vibrant cartoon style scene"),
            ("realistic", "Photorealistic scene"),
            ("artistic", "Artistic illustration"),
            ("unknown", "Scene showing")  # Default
        ]
        
        for media_type, expected_prefix in style_tests:
            scenes = generate_fallback_scenes(script, 1, media_type)
            assert expected_prefix in scenes[0].image_prompt


class TestImageGenerationUtils:
    """Test image generation utility functions."""
    
    @patch("requests.post")
    def test_generate_image_runware_success(self, mock_post):
        """Test successful Runware image generation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{
            "taskUUID": "test-uuid",
            "imageURL": "https://example.com/test_image.jpg"
        }]
        mock_post.return_value = mock_response
        
        scene = ScenePrompt(
            scene_number=1,
            scene_title="Test Scene",
            script_excerpt="Test excerpt",
            image_prompt="Test prompt"
        )
        
        result = generate_image_runware(scene, "runware:101@1")
        assert result == "https://example.com/test_image.jpg"
        
        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]["json"][0]["positivePrompt"] == "Test prompt"
        assert call_args[1]["json"][0]["model"] == "runware:101@1"
    
    @patch("requests.post")
    def test_generate_image_runware_failure(self, mock_post):
        """Test Runware image generation failure."""
        mock_post.side_effect = requests.exceptions.RequestException("API Error")
        
        scene = ScenePrompt(
            scene_number=1,
            scene_title="Test",
            script_excerpt="Test",
            image_prompt="Test prompt"
        )
        
        result = generate_image_runware(scene, "runware:101@1")
        assert result is None
    
    @patch("requests.post")
    def test_generate_image_together_success(self, mock_post):
        """Test successful Together AI image generation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{
                "url": "https://example.com/together_image.jpg"
            }]
        }
        mock_post.return_value = mock_response
        
        scene = ScenePrompt(
            scene_number=1,
            scene_title="Test Scene",
            script_excerpt="Test excerpt",
            image_prompt="Test image prompt"
        )
        
        result = generate_image_together(scene, "black-forest-labs/FLUX.1-schnell-Free")
        assert result == "https://example.com/together_image.jpg"
        
        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]["json"]["prompt"] == "Test image prompt"
        assert call_args[1]["json"]["model"] == "black-forest-labs/FLUX.1-schnell-Free"
        assert call_args[1]["json"]["steps"] == 4  # schnell model
    
    @patch("backend.utils.image_generation.generate_image_runware")
    @patch("backend.utils.image_generation.generate_image_together")
    def test_generate_image_with_retry_success(self, mock_together, mock_runware):
        """Test successful image generation with retry logic."""
        mock_runware.return_value = "https://example.com/success_image.jpg"
        
        scene = ScenePrompt(
            scene_number=1,
            scene_title="Test Scene",
            script_excerpt="Test excerpt",
            image_prompt="Test prompt"
        )
        
        result = generate_image_with_retry(scene, "runware", "runware:101@1")
        
        assert isinstance(result, PreviewImage)
        assert result.scene_number == 1
        assert result.scene_title == "Test Scene"
        assert result.prompt == "Test prompt"
        assert result.preview_url == "https://example.com/success_image.jpg"
        assert result.provider_used == "runware"
        assert result.model_used == "runware:101@1"
        assert result.approved is False
        assert result.error is None
        assert result.generation_time > 0
        
        mock_runware.assert_called_once_with(scene, "runware:101@1")
        mock_together.assert_not_called()
    
    @patch("backend.utils.image_generation.generate_image_runware")
    def test_generate_image_with_retry_failure(self, mock_runware):
        """Test image generation failure with retry logic."""
        mock_runware.return_value = None  # Simulate failure
        
        scene = ScenePrompt(
            scene_number=1,
            scene_title="Test Scene",
            script_excerpt="Test excerpt",
            image_prompt="Test prompt"
        )
        
        result = generate_image_with_retry(scene, "runware", "runware:101@1")
        
        assert isinstance(result, PreviewImage)
        assert result.scene_number == 1
        assert result.preview_url == ""
        assert result.error is not None
        assert "Failed to generate" in result.error
    
    def test_generate_image_with_retry_unknown_provider(self):
        """Test image generation with unknown provider."""
        scene = ScenePrompt(
            scene_number=1,
            scene_title="Test Scene", 
            script_excerpt="Test excerpt",
            image_prompt="Test prompt"
        )
        
        result = generate_image_with_retry(scene, "unknown_provider", "model")
        
        assert result.preview_url == ""
        assert result.error == "Unknown provider: unknown_provider"


class TestStorageUtils:
    """Test storage utility functions."""
    
    def test_save_scene_prompts(self, temp_projects_dir, sample_scene_prompts):
        """Test saving scene prompts to file."""
        project_path = temp_projects_dir / "test_project"
        project_path.mkdir(parents=True, exist_ok=True)
        
        save_scene_prompts(project_path, sample_scene_prompts)
        
        prompts_file = project_path / "scene_prompts.txt"
        assert prompts_file.exists()
        
        content = prompts_file.read_text(encoding="utf-8")
        assert "Scene Prompts for Image Generation" in content
        
        for scene in sample_scene_prompts:
            assert f"Scene {scene.scene_number}: {scene.scene_title}" in content
            assert scene.script_excerpt in content
            assert scene.image_prompt in content
    
    @patch("requests.get")
    def test_save_approved_images_success(self, mock_get, temp_projects_dir):
        """Test saving approved images successfully."""
        mock_response = Mock()
        mock_response.content = b"fake_image_data"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Create test session with approved previews
        project_path = temp_projects_dir / "test_project"
        project_path.mkdir(parents=True, exist_ok=True)
        
        previews = [
            PreviewImage(
                scene_number=1,
                scene_title="Scene 1",
                prompt="Test prompt 1",
                preview_url="https://example.com/image1.jpg",
                generation_time=5.0,
                provider_used="runware",
                model_used="runware:101@1",
                approved=True
            ),
            PreviewImage(
                scene_number=2,
                scene_title="Scene 2", 
                prompt="Test prompt 2",
                preview_url="https://example.com/image2.jpg",
                generation_time=4.0,
                provider_used="runware",
                model_used="runware:101@1",
                approved=False  # Not approved
            )
        ]
        
        session = GenerationSession(
            session_id="test_session",
            project_id="test_project",
            status="previewing",
            total_scenes=2,
            completed_scenes=2,
            previews=previews
        )
        
        with patch("backend.utils.storage.PROJECTS_DIR", temp_projects_dir):
            saved_count = save_approved_images(session)
        
        assert saved_count == 1  # Only 1 approved image
        
        # Verify files were created
        images_dir = project_path / "images"
        assert images_dir.exists()
        assert (images_dir / "scene_001.jpg").exists()
        assert not (images_dir / "scene_002.jpg").exists()  # Not approved
    
    def test_list_projects_empty(self, temp_projects_dir):
        """Test listing projects when directory is empty."""
        with patch("backend.utils.storage.PROJECTS_DIR", temp_projects_dir):
            result = list_projects()
        
        assert "projects" in result
        assert isinstance(result["projects"], list)
        assert len(result["projects"]) == 0
    
    def test_get_project_details_success(self, temp_projects_dir, sample_analysis):
        """Test getting project details successfully."""
        project_id = "detail_test_project"
        script_content = "Detailed test script content"
        
        # Create project
        project_path = temp_projects_dir / project_id
        project_path.mkdir(parents=True, exist_ok=True)
        images_dir = project_path / "images"
        images_dir.mkdir(exist_ok=True)
        
        (project_path / "script.txt").write_text(script_content, encoding="utf-8")
        (project_path / "analysis.json").write_text(
            json.dumps(sample_analysis.dict(), indent=2), encoding="utf-8"
        )
        
        # Create some test images
        (images_dir / "scene_001.jpg").write_bytes(b"fake_image_1")
        (images_dir / "scene_002.jpg").write_bytes(b"fake_image_2")
        
        with patch("backend.utils.storage.PROJECTS_DIR", temp_projects_dir):
            result = get_project_details(project_id)
        
        assert result["project_id"] == project_id
        assert result["script"] == script_content
        assert result["analysis"]["word_count"] == sample_analysis.word_count
        assert result["total_images"] == 2
        assert len(result["images"]) == 2
        
        # Verify image paths
        expected_paths = [
            f"/projects/{project_id}/images/scene_001.jpg",
            f"/projects/{project_id}/images/scene_002.jpg"
        ]
        assert all(path in result["images"] for path in expected_paths)
    
    def test_get_project_details_nonexistent(self, temp_projects_dir):
        """Test getting details for non-existent project."""
        with patch("backend.utils.storage.PROJECTS_DIR", temp_projects_dir):
            with pytest.raises(FileNotFoundError, match="Project not found"):
                get_project_details("nonexistent_project")


@pytest.fixture
def sample_scene_prompts():
    """Sample scene prompts for testing."""
    return [
        ScenePrompt(
            scene_number=1,
            scene_title="Ruby in the Forest",
            script_excerpt="Once upon a time, in a magical forest...",
            image_prompt="Cinematic shot of a young fox with bright red fur"
        ),
        ScenePrompt(
            scene_number=2,
            scene_title="The Hidden Clearing",
            script_excerpt="Ruby discovered a hidden clearing...",
            image_prompt="Magical clearing with golden butterflies"
        )
    ]