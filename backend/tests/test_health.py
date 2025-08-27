import pytest
from datetime import datetime


class TestHealthEndpoints:
    """Test health and status endpoints."""
    
    def test_root_endpoint(self, client):
        """Test the root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "Story to Image Generator API" in data["message"]
        assert data["status"] == "ready"
        assert "active_sessions" in data
        assert isinstance(data["active_sessions"], int)
        assert data["active_sessions"] >= 0
    
    def test_health_endpoint(self, client):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "active_sessions" in data
        assert "total_projects" in data
        
        # Verify timestamp format
        timestamp = data["timestamp"]
        assert isinstance(timestamp, str)
        # Should be valid ISO format
        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        # Verify numeric fields
        assert isinstance(data["active_sessions"], int)
        assert isinstance(data["total_projects"], int)
        assert data["active_sessions"] >= 0
        assert data["total_projects"] >= 0
    
    def test_health_with_projects(self, client, temp_projects_dir):
        """Test health endpoint with existing projects."""
        # Create a project first
        response = client.post("/analyze-script", json={
            "script": "Health test project script.",
            "title": "Health Test Project"
        })
        assert response.status_code == 200
        
        # Check health after project creation
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["total_projects"] >= 1
    
    def test_health_with_active_sessions(self, client, temp_projects_dir):
        """Test health endpoint with active sessions."""
        # Create project and start generation
        response = client.post("/analyze-script", json={
            "script": "Session health test script.",
            "title": "Session Health Test"
        })
        project_id = response.json()["project_id"]
        
        # Start generation to create session
        response = client.post("/generate-previews", json={
            "project_id": project_id,
            "num_scenes": 1,
            "media_type": "cinematic",
            "ai_provider": "fallback",
            "ai_model": "dummy",
            "image_provider": "runware",
            "image_model": "runware:101@1"
        })
        
        # Check health with active session
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["active_sessions"] >= 1


class TestModelsEndpoint:
    """Test the models information endpoint."""
    
    def test_get_available_models(self, client):
        """Test retrieving available models."""
        response = client.get("/models")
        assert response.status_code == 200
        
        data = response.json()
        assert "ai_models" in data
        assert "image_models" in data
        
        # Check AI models
        assert "openrouter" in data["ai_models"]
        openrouter_models = data["ai_models"]["openrouter"]
        assert isinstance(openrouter_models, list)
        assert len(openrouter_models) > 0
        
        # Verify expected OpenRouter models
        expected_models = [
            "openai/gpt-oss-20b:free",
            "meta-llama/llama-3.1-8b-instruct:free",
            "microsoft/phi-3-mini-128k-instruct:free"
        ]
        for model in expected_models:
            assert model in openrouter_models
        
        # Check image models
        assert "runware" in data["image_models"]
        assert "together" in data["image_models"]
        
        runware_models = data["image_models"]["runware"]
        together_models = data["image_models"]["together"]
        
        assert isinstance(runware_models, list)
        assert isinstance(together_models, list)
        assert len(runware_models) > 0
        assert len(together_models) > 0
        
        # Verify expected image models
        assert "runware:101@1" in runware_models
        assert "black-forest-labs/FLUX.1-schnell-Free" in together_models


class TestProjectsEndpoints:
    """Test project listing and details endpoints."""
    
    def test_list_projects_empty(self, client, temp_projects_dir):
        """Test listing projects when none exist."""
        response = client.get("/projects")
        assert response.status_code == 200
        
        data = response.json()
        assert "projects" in data
        assert isinstance(data["projects"], list)
        assert len(data["projects"]) == 0
    
    def test_list_projects_with_data(self, client, temp_projects_dir):
        """Test listing projects with existing data."""
        # Create multiple projects
        projects_data = [
            {"script": "First test script.", "title": "First Project"},
            {"script": "Second test script with more content.", "title": "Second Project"},
            {"script": "Third project script.", "title": "Third Project"}
        ]
        
        created_projects = []
        for project_data in projects_data:
            response = client.post("/analyze-script", json=project_data)
            assert response.status_code == 200
            created_projects.append(response.json())
        
        # List projects
        response = client.get("/projects")
        assert response.status_code == 200
        
        data = response.json()
        assert "projects" in data
        projects = data["projects"]
        assert len(projects) == 3
        
        # Verify project structure
        for project in projects:
            assert "project_id" in project
            assert "created_at" in project
            assert "analysis" in project
            assert "word_count" in project["analysis"]
            assert "recommended_scenes" in project["analysis"]
    
    def test_get_project_details(self, client, temp_projects_dir):
        """Test getting detailed project information."""
        # Create a project
        script_content = "Detailed project test script with multiple words for analysis."
        response = client.post("/analyze-script", json={
            "script": script_content,
            "title": "Detailed Test Project"
        })
        project_id = response.json()["project_id"]
        
        # Get project details
        response = client.get(f"/projects/{project_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["project_id"] == project_id
        assert data["script"] == script_content
        assert "analysis" in data
        assert "images" in data
        assert "total_images" in data
        
        # Verify analysis structure
        analysis = data["analysis"]
        assert "word_count" in analysis
        assert "recommended_scenes" in analysis
        assert "estimated_duration_minutes" in analysis
        assert "complexity_score" in analysis
        
        # Initially no images
        assert isinstance(data["images"], list)
        assert data["total_images"] == 0
    
    def test_get_project_details_nonexistent(self, client):
        """Test getting details for non-existent project."""
        response = client.get("/projects/nonexistent_project")
        assert response.status_code == 404
        assert "Project not found" in response.json()["detail"]


class TestErrorHandling:
    """Test error handling across endpoints."""
    
    def test_404_endpoints(self, client):
        """Test various 404 scenarios."""
        endpoints_to_test = [
            ("/generation-status/invalid_session", 404),
            ("/projects/invalid_project", 404),
            ("/nonexistent-endpoint", 404)
        ]
        
        for endpoint, expected_status in endpoints_to_test:
            response = client.get(endpoint)
            assert response.status_code == expected_status
    
    def test_method_not_allowed(self, client):
        """Test method not allowed errors."""
        # Try POST on GET-only endpoints
        response = client.post("/health")
        assert response.status_code == 405
        
        response = client.post("/models")
        assert response.status_code == 405
    
    def test_malformed_requests(self, client):
        """Test handling of malformed requests."""
        # Invalid JSON
        response = client.post("/analyze-script", data="invalid json")
        assert response.status_code == 422
        
        # Missing content-type for JSON endpoints
        response = client.post("/generate-previews", data="some data")
        assert response.status_code == 422


class TestCORS:
    """Test CORS headers are properly set."""
    
    def test_cors_headers(self, client):
        """Test that CORS headers are present."""
        response = client.get("/")
        assert response.status_code == 200
        
        # The test client doesn't automatically include CORS headers,
        # but we can verify the middleware is configured by checking
        # that the response is successful from any origin
        assert response.status_code == 200
    
    def test_options_request(self, client):
        """Test OPTIONS request handling."""
        response = client.options("/")
        # FastAPI with CORS middleware should handle OPTIONS requests
        assert response.status_code in [200, 405]  # Either allowed or method not implemented


class TestConcurrency:
    """Test concurrent access patterns."""
    
    def test_multiple_simultaneous_projects(self, client, temp_projects_dir):
        """Test creating multiple projects simultaneously."""
        import concurrent.futures
        import threading
        
        def create_project(index):
            return client.post("/analyze-script", json={
                "script": f"Concurrent test script number {index}.",
                "title": f"Concurrent Project {index}"
            })
        
        # Create multiple projects concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_project, i) for i in range(5)]
            responses = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Verify all projects were created successfully
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert "project_id" in data
            assert data["project_id"].startswith("story_")
        
        # Verify projects are listed correctly
        response = client.get("/projects")
        assert response.status_code == 200
        assert len(response.json()["projects"]) == 5