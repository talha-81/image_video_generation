from pydantic import BaseModel
from typing import List, Dict, Optional

class ScriptAnalysis(BaseModel):
    word_count: int
    recommended_scenes: int
    estimated_duration_minutes: float
    complexity_score: str

class ScriptRequest(BaseModel):
    script: str
    title: str = "Untitled Story"

class ProjectInfo(BaseModel):
    project_id: str
    title: str
    created_at: str
    analysis: ScriptAnalysis
    script_content: str

class ScenePrompt(BaseModel):
    scene_number: int
    scene_title: str
    script_excerpt: str
    image_prompt: str

class GenerationRequest(BaseModel):
    project_id: str
    num_scenes: int
    media_type: str = "cinematic"      # "cinematic", "cartoon", "realistic", "artistic"
    ai_provider: str = "openrouter"    # "openrouter", "fallback"
    ai_model: str = "openai/gpt-4o-mini"
    image_provider: str = "runware"    # "runware", "together", "openrouter_imgae"
    image_model: str = "runware:101@1"

class RegenerationRequest(BaseModel):
    session_id: str
    scene_number: int
    image_provider: str = "runware"
    image_model: str = "runware:101@1"

class PreviewImage(BaseModel):
    scene_number: int
    scene_title: str
    prompt: str
    preview_url: str
    generation_time: float
    provider_used: str
    model_used: str
    approved: bool = False
    error: Optional[str] = None

class GenerationSession(BaseModel):
    session_id: str
    project_id: str
    status: str
    total_scenes: int
    completed_scenes: int
    previews: List[PreviewImage]
    scene_prompts: List[ScenePrompt] = []
    errors: List[str] = []

class ApprovalRequest(BaseModel):
    session_id: str
    scene_approvals: Dict[int, bool]