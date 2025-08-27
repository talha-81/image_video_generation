import pytest
import time
import json
from .conftest import wait_for_generation_completion

class TestImageGenerationEndpoint:
    """Test image generation endpoints."""
    
    def test_generate_previews_fallback(self, client, temp_projects_dir):
        """Test preview generation using fallback provider."""
        # Create project first
        script_payload = {
            "script": "A hero walks through a forest. The sun sets behind mountains.",
            "title": "Generation Test"
        }
        response = client.post("/analyze-script", json=script_payload)
        project_id = response.json()["project_id"]
        
        # Generate previews with fallback
        generation_payload = {
            "project_id": project_id,
            "num_scenes": 2,
            "media_type": "cinematic",
            "ai_provider": "fallback",  # Use fallback to avoid API calls
            "ai_model": "dummy",
            "image_provider": "runware",
            "image_model": "runware:101@1"
        }
        
        response = client.post("/generate-previews", json=generation_payload)
        assert response.status_code == 200
        
        data = response.json()
        assert "session_id" in data
        assert data["status"] == "generating"
        assert data["total_scenes"] == 2
        
        session_id = data["session_id"]
        
        # Wait for generation to complete
        final_status = wait_for_generation_completion(client, session_id)
        assert final_status is not None
        assert final_status["total_scenes"] == 2
        assert len(final_status["scene_prompts"]) == 2
        
        # Verify scene prompts structure
        for prompt in final_status["scene_prompts"]:
            assert "scene_number" in prompt
            assert "scene_title" in prompt
            assert "script_excerpt" in prompt
            assert "image_prompt" in prompt
    
    @pytest.mark.parametrize("media_type,expected_style", [
        ("cinematic", "Cinematic shot with dramatic lighting"),
        ("cartoon", "Vibrant cartoon style scene"),
        ("realistic", "Photorealistic scene"),
        ("artistic", "Artistic illustration")
    ])
    def test_generate_previews_different_styles(self, client, temp_projects_dir, media_type, expected_style):
        """Test preview generation with different media types."""
        # Create project
        response = client.post("/analyze-script", json={
            "script": "A magical story happens here.",
            "title": f"{media_type.title()} Test"
        })
        project_id = response.json()["project_id"]
        
        # Generate with specific style
        response = client.post("/generate-previews", json={
            "project_id": project_id,
            "num_scenes": 1,
            "media_type": media_type,
            "ai_provider": "fallback",
            "ai_model": "dummy",
            "image_provider": "runware",
            "image_model": "runware:101@1"
        })
        
        session_id = response.json()["session_id"]
        final_status = wait_for_generation_completion(client, session_id)
        
        # Check that style is reflected in prompts
        scene_prompt = final_status["scene_prompts"][0]
        assert expected_style in scene_prompt["image_prompt"]
    
    def test_generate_previews_with_openrouter(self, client, temp_projects_dir, mock_openrouter_success):
        """Test preview generation with mocked OpenRouter."""
        # Create project
        response = client.post("/analyze-script", json={
            "script": "A test story for OpenRouter generation.",
            "title": "OpenRouter Test"
        })
        project_id = response.json()["project_id"]
        
        # Generate with OpenRouter
        response = client.post("/generate-previews", json={
            "project_id": project_id,
            "num_scenes": 2,
            "media_type": "cinematic",
            "ai_provider": "openrouter",
            "ai_model": "openai/gpt-3.5-turbo",
            "image_provider": "runware",
            "image_model": "runware:101@1"
        })
        
        session_id = response.json()["session_id"]
        final_status = wait_for_generation_completion(client, session_id)
        
        # Verify OpenRouter was called and scenes were generated
        assert len(final_status["scene_prompts"]) == 2
        assert final_status["scene_prompts"][0]["scene_title"] == "Ruby in the Forest"
        assert final_status["scene_prompts"][1]["scene_title"] == "The Hidden Clearing"
    
    def test_generate_previews_nonexistent_project(self, client):
        """Test error handling for non-existent project."""
        response = client.post("/generate-previews", json={
            "project_id": "nonexistent_project",
            "num_scenes": 2,
            "media_type": "cinematic",
            "ai_provider": "fallback",
            "ai_model": "dummy",
            "image_provider": "runware",
            "image_model": "runware:101@1"
        })
        
        assert response.status_code == 404
        assert "Project not found" in response.json()["detail"]
    
    def test_generation_status(self, client, temp_projects_dir):
        """Test generation status endpoint."""
        # Create project and start generation
        response = client.post("/analyze-script", json={
            "script": "Status test story.",
            "title": "Status Test"
        })
        project_id = response.json()["project_id"]
        
        response = client.post("/generate-previews", json={
            "project_id": project_id,
            "num_scenes": 1,
            "media_type": "cinematic",
            "ai_provider": "fallback",
            "ai_model": "dummy",
            "image_provider": "runware",
            "image_model": "runware:101@1"
        })
        
        session_id = response.json()["session_id"]
        
        # Check status
        response = client.get(f"/generation-status/{session_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["session_id"] == session_id
        assert data["project_id"] == project_id
        assert data["status"] in ["generating", "previewing", "completed"]
        assert data["total_scenes"] == 1
        assert "completed_scenes" in data
        assert "previews" in data
        assert "scene_prompts" in data
        assert "errors" in data
    
    def test_generation_status_nonexistent_session(self, client):
        """Test error handling for non-existent session."""
        response = client.get("/generation-status/nonexistent_session")
        assert response.status_code == 404
        assert "Session not found" in response.json()["detail"]


class TestImageRegenerationEndpoint:
    """Test scene regeneration functionality."""
    
    def test_regenerate_scene(self, client, temp_projects_dir, mock_image_generation_success):
        """Test regenerating a single scene."""
        # Create project and generate initial previews
        response = client.post("/analyze-script", json={
            "script": "Scene regeneration test story with multiple scenes.",
            "title": "Regeneration Test"
        })
        project_id = response.json()["project_id"]
        
        response = client.post("/generate-previews", json={
            "project_id": project_id,
            "num_scenes": 2,
            "media_type": "cartoon",
            "ai_provider": "fallback",
            "ai_model": "dummy",
            "image_provider": "runware",
            "image_model": "runware:101@1"
        })
        
        session_id = response.json()["session_id"]
        
        # Wait for initial generation
        status = wait_for_generation_completion(client, session_id)
        scene_number = status["scene_prompts"][0]["scene_number"]
        
        # Regenerate first scene
        response = client.post("/regenerate-scene", json={
            "session_id": session_id,
            "scene_number": scene_number,
            "image_provider": "runware",
            "image_model": "runware:101@1"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["scene_number"] == scene_number
        assert "new_preview" in data
    
    def test_regenerate_nonexistent_session(self, client):
        """Test regeneration with non-existent session."""
        response = client.post("/regenerate-scene", json={
            "session_id": "nonexistent_session",
            "scene_number": 1,
            "image_provider": "runware",
            "image_model": "runware:101@1"
        })
        
        assert response.status_code == 404
        assert "Session not found" in response.json()["detail"]
    
    def test_regenerate_nonexistent_scene(self, client, temp_projects_dir):
        """Test regeneration with non-existent scene number."""
        # Create session first
        response = client.post("/analyze-script", json={
            "script": "Test for nonexistent scene.",
            "title": "Scene Error Test"
        })
        project_id = response.json()["project_id"]
        
        response = client.post("/generate-previews", json={
            "project_id": project_id,
            "num_scenes": 1,
            "media_type": "cinematic",
            "ai_provider": "fallback",
            "ai_model": "dummy",
            "image_provider": "runware",
            "image_model": "runware:101@1"
        })
        
        session_id = response.json()["session_id"]
        
        # Try to regenerate non-existent scene
        response = client.post("/regenerate-scene", json={
            "session_id": session_id,
            "scene_number": 999,  # Non-existent scene
            "image_provider": "runware",
            "image_model": "runware:101@1"
        })
        
        assert response.status_code == 404
        assert "Scene not found" in response.json()["detail"]


class TestApprovalEndpoint:
    """Test preview approval functionality."""
    
    def test_approve_previews(self, client, temp_projects_dir, mock_image_download):
        """Test approving previews and saving images."""
        # Create project and generate previews
        response = client.post("/analyze-script", json={
            "script": "Approval test story with scenes to approve.",
            "title": "Approval Test"
        })
        project_id = response.json()["project_id"]
        
        response = client.post("/generate-previews", json={
            "project_id": project_id,
            "num_scenes": 2,
            "media_type": "realistic",
            "ai_provider": "fallback",
            "ai_model": "dummy",
            "image_provider": "runware",
            "image_model": "runware:101@1"
        })
        
        session_id = response.json()["session_id"]
        
        # Wait for generation
        status = wait_for_generation_completion(client, session_id)
        
        # Approve all scenes
        scene_numbers = [prompt["scene_number"] for prompt in status["scene_prompts"]]
        approvals = {str(num): True for num in scene_numbers}
        
        response = client.post("/approve-previews", json={
            "session_id": session_id,
            "scene_approvals": approvals
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["total_scenes"] == 2
        assert "saved_images" in data
    
    def test_approve_partial_previews(self, client, temp_projects_dir):
        """Test approving only some previews."""
        # Create project with multiple scenes
        response = client.post("/analyze-script", json={
            "script": "Partial approval test with multiple scenes for selective approval.",
            "title": "Partial Approval Test"
        })
        project_id = response.json()["project_id"]
        
        response = client.post("/generate-previews", json={
            "project_id": project_id,
            "num_scenes": 3,
            "media_type": "artistic",
            "ai_provider": "fallback",
            "ai_model": "dummy",
            "image_provider": "runware",
            "image_model": "runware:101@1"
        })
        
        session_id = response.json()["session_id"]
        status = wait_for_generation_completion(client, session_id)
        
        # Approve only first and third scenes
        scene_numbers = [prompt["scene_number"] for prompt in status["scene_prompts"]]
        approvals = {
            str(scene_numbers[0]): True,
            str(scene_numbers[1]): False,
            str(scene_numbers[2]): True
        }
        
        response = client.post("/approve-previews", json={
            "session_id": session_id,
            "scene_approvals": approvals
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
    
    def test_approve_nonexistent_session(self, client):
        """Test approval with non-existent session."""
        response = client.post("/approve-previews", json={
            "session_id": "nonexistent_session",
            "scene_approvals": {"1": True}
        })
        
        assert response.status_code == 404
        assert "Session not found" in response.json()["detail"]


class TestSessionCleanup:
    """Test session management and cleanup."""
    
    def test_cleanup_session(self, client, temp_projects_dir):
        """Test manual session cleanup."""
        # Create a session
        response = client.post("/analyze-script", json={
            "script": "Cleanup test story.",
            "title": "Cleanup Test"
        })
        project_id = response.json()["project_id"]
        
        response = client.post("/generate-previews", json={
            "project_id": project_id,
            "num_scenes": 1,
            "media_type": "cinematic",
            "ai_provider": "fallback",
            "ai_model": "dummy",
            "image_provider": "runware",
            "image_model": "runware:101@1"
        })
        
        session_id = response.json()["session_id"]
        
        # Verify session exists
        response = client.get(f"/generation-status/{session_id}")
        assert response.status_code == 200
        
        # Cleanup session
        response = client.delete(f"/sessions/{session_id}")
        assert response.status_code == 200
        assert response.json()["message"] == "Session cleaned up"
        
        # Verify session no longer exists
        response = client.get(f"/generation-status/{session_id}")
        assert response.status_code == 404
    
    def test_cleanup_nonexistent_session(self, client):
        """Test cleanup of non-existent session."""
        response = client.delete("/sessions/nonexistent_session")
        assert response.status_code == 404
        assert "Session not found" in response.json()["detail"]


class TestGenerationValidation:
    """Test input validation for generation endpoints."""
    
    def test_invalid_generation_request(self, client, temp_projects_dir):
        """Test validation of generation request."""
        # Create project first
        response = client.post("/analyze-script", json={
            "script": "Validation test story.",
            "title": "Validation Test"
        })
        project_id = response.json()["project_id"]
        
        # Test missing required fields
        response = client.post("/generate-previews", json={
            "project_id": project_id
            # Missing num_scenes
        })
        assert response.status_code == 422  # Validation error
    
    def test_invalid_num_scenes(self, client, temp_projects_dir):
        """Test validation of num_scenes parameter."""
        response = client.post("/analyze-script", json={
            "script": "Validation test story.",
            "title": "Validation Test"
        })
        project_id = response.json()["project_id"]
        
        # Test invalid num_scenes type
        response = client.post("/generate-previews", json={
            "project_id": project_id,
            "num_scenes": "not_a_number",
            "media_type": "cinematic",
            "ai_provider": "fallback",
            "ai_model": "dummy",
            "image_provider": "runware",
            "image_model": "runware:101@1"
        })
        assert response.status_code == 422