import pytest
import json
from backend.utils.script_analysis import analyze_script, create_project


class TestScriptAnalysisEndpoint:
    """Test the /analyze-script endpoint."""
    
    def test_analyze_script_success(self, client, temp_projects_dir):
        """Test successful script analysis."""
        payload = {
            "script": "Once upon a time there was a hero who saved the world.",
            "title": "Test Story"
        }
        
        response = client.post("/analyze-script", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["title"] == "Test Story"
        assert data["analysis"]["word_count"] == 12
        assert data["analysis"]["recommended_scenes"] == 2
        assert "project_id" in data
        assert data["project_id"].startswith("story_")
        assert "created_at" in data
        
        # Verify project was created on disk
        project_path = temp_projects_dir / data["project_id"]
        assert project_path.exists()
        assert (project_path / "script.txt").exists()
        assert (project_path / "analysis.json").exists()
    
    def test_analyze_script_default_title(self, client, temp_projects_dir):
        """Test script analysis with default title."""
        payload = {"script": "A short test script."}
        
        response = client.post("/analyze-script", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["title"] == "Untitled Story"
    
    def test_analyze_empty_script(self, client, temp_projects_dir):
        """Test analysis of empty script."""
        payload = {"script": "", "title": "Empty Story"}
        
        response = client.post("/analyze-script", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["analysis"]["word_count"] == 0
        assert data["analysis"]["recommended_scenes"] == 2
    
    def test_analyze_long_script(self, client, temp_projects_dir):
        """Test analysis of a longer script."""
        long_script = " ".join(["word"] * 500)  # 500 words
        payload = {"script": long_script, "title": "Long Story"}
        
        response = client.post("/analyze-script", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["analysis"]["word_count"] == 500
        assert data["analysis"]["recommended_scenes"] == 6  # Based on word count ranges
        assert data["analysis"]["estimated_duration_minutes"] == 2.5  # 500/200
    
    def test_analyze_script_missing_script(self, client):
        """Test error handling for missing script."""
        payload = {"title": "No Script Story"}
        
        response = client.post("/analyze-script", json=payload)
        assert response.status_code == 422  # Validation error
    
    def test_analyze_script_invalid_json(self, client):
        """Test error handling for invalid JSON."""
        response = client.post("/analyze-script", data="invalid json")
        assert response.status_code == 422


class TestScriptAnalysisUtils:
    """Test script analysis utility functions."""
    
    def test_analyze_script_word_count(self):
        """Test word count calculation."""
        script = "The quick brown fox jumps over the lazy dog."
        analysis = analyze_script(script)
        assert analysis.word_count == 9
    
    def test_analyze_script_recommended_scenes(self):
        """Test recommended scenes calculation."""
        test_cases = [
            ("short script", 2),  # < 100 words
            (" ".join(["word"] * 150), 4),  # 100-300 words
            (" ".join(["word"] * 450), 6),  # 300-600 words
            (" ".join(["word"] * 750), 9),  # 600-900 words
            (" ".join(["word"] * 1200), 10),  # > 900 words, capped at 10
        ]
        
        for script, expected_scenes in test_cases:
            analysis = analyze_script(script)
            assert analysis.recommended_scenes == expected_scenes
    
    def test_analyze_script_complexity(self):
        """Test complexity score calculation."""
        simple_script = "cat dog run jump play"
        complex_script = "magnificent extraordinary phenomenal unbelievable"
        
        simple_analysis = analyze_script(simple_script)
        complex_analysis = analyze_script(complex_script)
        
        assert simple_analysis.complexity_score == "Simple"
        assert complex_analysis.complexity_score == "Complex"
    
    def test_analyze_script_duration(self):
        """Test estimated duration calculation."""
        script = " ".join(["word"] * 200)  # Exactly 200 words
        analysis = analyze_script(script)
        assert analysis.estimated_duration_minutes == 1.0  # 200/200 = 1.0
    
    def test_create_project(self, temp_projects_dir, sample_analysis):
        """Test project creation."""
        project_id = "test_project"
        script = "Test script content"
        
        project_path = create_project(project_id, script, sample_analysis)
        
        # Verify directory structure
        assert project_path.exists()
        assert (project_path / "images").exists()
        
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


class TestProjectStorage:
    """Test project storage and retrieval."""
    
    def test_project_files_created(self, client, temp_projects_dir):
        """Test that project files are properly created."""
        payload = {"script": "Test script for file creation", "title": "File Test"}
        
        response = client.post("/analyze-script", json=payload)
        project_id = response.json()["project_id"]
        
        project_path = temp_projects_dir / project_id
        
        # Check directory structure
        assert project_path.is_dir()
        assert (project_path / "images").is_dir()
        
        # Check files
        script_file = project_path / "script.txt"
        analysis_file = project_path / "analysis.json"
        
        assert script_file.is_file()
        assert analysis_file.is_file()
        
        # Verify script content
        script_content = script_file.read_text(encoding="utf-8")
        assert script_content == "Test script for file creation"
        
        # Verify analysis content
        analysis_content = json.loads(analysis_file.read_text(encoding="utf-8"))
        assert "word_count" in analysis_content
        assert "recommended_scenes" in analysis_content
        assert "estimated_duration_minutes" in analysis_content
        assert "complexity_score" in analysis_content