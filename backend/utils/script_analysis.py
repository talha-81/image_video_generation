import json
from datetime import datetime
from pathlib import Path
from ..models.schemas import ScriptAnalysis
from ..config import PROJECTS_DIR

def analyze_script(script: str) -> ScriptAnalysis:
    """Analyze script and provide recommendations."""
    words = script.split()
    word_count = len(words)

    # Determine recommended scenes based on word count
    if word_count < 100:
        recommended_scenes = 2
    elif word_count < 300:
        recommended_scenes = 4
    elif word_count < 600:
        recommended_scenes = 6
    elif word_count < 900:
        recommended_scenes = 9
    else:
        recommended_scenes = min(10, word_count // 100)

    # Calculate metrics
    estimated_minutes = word_count / 200.0  # Average reading speed
    avg_word_length = sum(len(word) for word in words) / max(word_count, 1)
    complexity = "Complex" if avg_word_length > 6 else "Simple"

    return ScriptAnalysis(
        word_count=word_count,
        recommended_scenes=recommended_scenes,
        estimated_duration_minutes=round(estimated_minutes, 1),
        complexity_score=complexity
    )

def create_project(project_id: str, script: str, analysis: ScriptAnalysis) -> Path:
    """Create a new project directory with script and analysis."""
    project_path = PROJECTS_DIR / project_id
    
    # Create directory structure
    project_path.mkdir(parents=True, exist_ok=True)
    (project_path / "images").mkdir(exist_ok=True)
    
    # Save files
    (project_path / "script.txt").write_text(script, encoding="utf-8")
    (project_path / "analysis.json").write_text(
        json.dumps(analysis.dict(), indent=2), 
        encoding="utf-8"
    )
    
    return project_path
