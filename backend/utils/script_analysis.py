import json
from datetime import datetime
from pathlib import Path
import re
from typing import List
import requests
from ..models.schemas import ScriptAnalysis
from ..config import PROJECTS_DIR

def analyze_script(script: str) -> ScriptAnalysis:
    """Analyze script and provide enhanced AI-like recommendations with improved accuracy."""
    # Word-level analysis
    words = [word for word in script.split() if word.strip()]
    word_count = len(words)

    # Sentence and paragraph analysis with refined regex
    sentences = re.split(r'[.!?]+(?:\s+|$)', script)
    sentences = [s.strip() for s in sentences if s.strip() and len(s) > 1]
    sentence_count = len(sentences)
    avg_sentence_length = word_count / max(sentence_count, 1)

    paragraphs = [p.strip() for p in script.split("\n\n") if p.strip()]
    paragraph_count = len(paragraphs)

    # Vocabulary richness with enhanced cleaning
    unique_words = set(
        re.sub(r'[^\w\s]', '', word.lower()) 
        for word in words 
        if re.sub(r'[^\w\s]', '', word)
    )
    vocab_richness = len(unique_words) / max(word_count, 1)

    # Smart scene recommendation with contextual analysis
    dialogue_indicators = len(re.findall(r'["“”](.*?)(?:["“”]|$)', script, re.DOTALL))
    action_indicators = len(re.findall(r'\b(?:INT\.|EXT\.|[A-Z]+\s*\([^)]+\))', script, re.IGNORECASE))
    
    if paragraph_count > 1 or action_indicators > 0:
        recommended_scenes = min(15, paragraph_count + max(0, action_indicators - 1))
    elif dialogue_indicators > sentence_count // 2:
        recommended_scenes = max(2, min(12, sentence_count // 2))
    else:
        recommended_scenes = max(1, min(10, sentence_count // 4))

    # Enhanced duration estimation with genre-aware pacing
    base_minutes = word_count / 180.0  # Adjusted reading speed for scripts
    pacing_factor = 1.0
    if dialogue_indicators > sentence_count * 0.6:
        pacing_factor = 1.2  # Dialogue-heavy scripts are slower
    elif action_indicators > paragraph_count * 0.3:
        pacing_factor = 0.9  # Action-heavy scripts are faster
    else:
        pacing_factor = 1.0 + (avg_sentence_length / 25.0)  # Neutral pacing
    estimated_minutes = base_minutes * pacing_factor

    # Advanced complexity scoring
    avg_word_length = sum(len(re.sub(r'[^\w]', '', word)) for word in words) / max(word_count, 1)
    long_words = len([word for word in words if len(re.sub(r'[^\w]', '', word)) > 8])
    long_word_ratio = long_words / max(word_count, 1)

    if avg_word_length > 6.5 or vocab_richness > 0.55 or long_word_ratio > 0.15:
        complexity = "Complex"
    elif avg_word_length > 5.0 or vocab_richness > 0.45 or long_word_ratio > 0.08:
        complexity = "Moderate"
    else:
        complexity = "Simple"

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
