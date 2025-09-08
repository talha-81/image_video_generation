# Complete fix for backend/main.py
# Replace your existing main.py with this corrected version

import uuid
import json
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
from contextlib import asynccontextmanager

from .config import CONFIG, PROJECTS_DIR
from .models.schemas import (
    ScriptAnalysis, ScriptRequest, ProjectInfo, ScenePrompt, 
    GenerationRequest, RegenerationRequest, PreviewImage, 
    GenerationSession, ApprovalRequest
)
from .models.session_manager import get_session, set_session, delete_session, count_sessions
from .utils.script_analysis import analyze_script, create_project
from .utils.prompt_generation import generate_scene_prompts_Openai, generate_fallback_scenes
from .utils.image_generation import generate_image_with_retry
from .utils.storage import save_scene_prompts, save_approved_images

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Story to Image Generator API starting...")
    print(f"📁 Projects directory: {PROJECTS_DIR}")

    providers = {
        "Runware": CONFIG["runware"]["api_key"] != "your_key_here",
        "Together AI": CONFIG["together"]["api_key"] != "your_key_here", 
        "Openai": CONFIG["Openai"]["api_key"] != "your_key_here",
    }
    for name, available in providers.items():
        print(f"{'✅' if available else '❌'} {name}")

    print("\n🧠 Available AI Models (Openai):")
    for model in CONFIG["Openai"]["models"]:
        print(f"  • {model}")

    print("\n🎨 Image Models:")
    print("  Runware:")
    for model in CONFIG["runware"]["models"]:
        print(f"  • {model}")
    print("  Together AI:")
    for model in CONFIG["together"]["models"]:
        print(f"  • {model}")

    yield
    print("🛑 Shutting down...")

app = FastAPI(
    title="Story to Image Generator",
    description="Transform stories into images with AI",
    version="3.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.mount("/projects", StaticFiles(directory=PROJECTS_DIR), name="projects")

@app.get("/")
async def root():
    return {
        "message": "Story to Image Generator API ",
        "status": "ready",
        "active_sessions": count_sessions()
    }

@app.get("/models")
async def get_available_models():
    return {
        "ai_models": {"Openai": CONFIG["Openai"]["models"]},
        "image_models": {
            "runware": CONFIG["runware"]["models"], 
            "together": CONFIG["together"]["models"],        }
    }

@app.post("/analyze-script", response_model=ProjectInfo)
async def analyze_script_endpoint(req: ScriptRequest):
    try:
        project_id = f"story_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        analysis = analyze_script(req.script)
        create_project(project_id, req.script, analysis)
        
        return ProjectInfo(
            project_id=project_id,
            title=req.title,
            created_at=datetime.now().isoformat(),
            analysis=analysis,
            script_content=req.script
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/generate-previews")
async def generate_previews(request: GenerationRequest, background_tasks: BackgroundTasks):
    project_path = PROJECTS_DIR / request.project_id
    if not project_path.exists():
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        script = (project_path / "script.txt").read_text(encoding="utf-8")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Script file not found")

    # Generate scene prompts
    if request.ai_provider == "Openai":
        scenes = generate_scene_prompts_Openai(
            script, request.num_scenes, request.media_type, request.ai_model
        )
    else:
        scenes = generate_fallback_scenes(script, request.num_scenes, request.media_type)

    save_scene_prompts(project_path, scenes)

    # Create generation session
    session_id = f"session_{uuid.uuid4().hex[:8]}"
    session = GenerationSession(
        session_id=session_id,
        project_id=request.project_id,
        status="generating",
        total_scenes=len(scenes),
        completed_scenes=0,
        previews=[],
        scene_prompts=scenes,
        errors=[]
    )
    set_session(session)

    # Generate previews in background
    def generate_previews_task():
        current_session = get_session(session_id)
        if not current_session:
            return
        
        try:
            for scene_prompt in scenes:
                preview = generate_image_with_retry(
                    scene_prompt, request.image_provider, request.image_model
                )
                current_session.previews.append(preview)
                current_session.completed_scenes += 1
                
                if not preview.preview_url:
                    error_msg = f"Failed to generate scene {scene_prompt.scene_number}"
                    current_session.errors.append(error_msg)
                
                set_session(current_session)  # Update session state
            
            current_session.status = "previewing"
            set_session(current_session)
            
        except Exception as e:
            current_session.status = "failed"
            current_session.errors.append(f"Generation failed: {str(e)}")
            set_session(current_session)

    background_tasks.add_task(generate_previews_task)

    return {
        "session_id": session_id, 
        "status": "generating", 
        "total_scenes": len(scenes)
    }

@app.post("/regenerate-scene")
async def regenerate_scene(request: RegenerationRequest):
    session = get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Find the scene prompt
    scene_prompt = next(
        (p for p in session.scene_prompts if p.scene_number == request.scene_number), 
        None
    )
    if not scene_prompt:
        raise HTTPException(status_code=404, detail="Scene not found")

    # Generate new preview
    preview = generate_image_with_retry(
        scene_prompt, request.image_provider, request.image_model
    )

    # Update session with new preview
    replaced = False
    for i, existing_preview in enumerate(session.previews):
        if existing_preview.scene_number == request.scene_number:
            session.previews[i] = preview
            replaced = True
            break
    
    if not replaced:
        session.previews.append(preview)

    if not preview.preview_url:
        session.errors.append(f"Failed to regenerate scene {request.scene_number}")

    set_session(session)

    return {
        "status": "success" if preview.preview_url else "failed",
        "scene_number": request.scene_number,
        "new_preview": preview
    }

@app.get("/generation-status/{session_id}")
async def get_generation_status(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@app.post("/approve-previews")
async def approve_previews(request: ApprovalRequest):
    session = get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Update approval status for each scene
    for scene_num, approved in request.scene_approvals.items():
        for preview in session.previews:
            if preview.scene_number == int(scene_num):
                preview.approved = approved
                break

    # Save approved images
    try:
        saved_count = save_approved_images(session)
        session.status = "completed"
        set_session(session)

        return {
            "status": "completed",
            "saved_images": saved_count,
            "total_scenes": len(session.previews)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save images: {str(e)}")

@app.get("/projects")
async def list_projects():
    from .utils.storage import list_projects as _list_projects
    return _list_projects()

@app.get("/projects/{project_id}")
async def get_project_details(project_id: str):
    from .utils.storage import get_project_details as _get_project_details
    try:
        return _get_project_details(project_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Project not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading project: {str(e)}")

# NEW: Add catch-all route for direct project access (fixes the 404 issue)
@app.get("/story_{timestamp}")
async def get_story_project_direct(timestamp: str):
    """Handle direct story project access - common cause of 404 errors"""
    project_id = f"story_{timestamp}"
    return await get_project_details(project_id)

@app.delete("/sessions/{session_id}")
async def cleanup_session(session_id: str):
    if delete_session(session_id):
        return {"message": "Session cleaned up"}
    raise HTTPException(status_code=404, detail="Session not found")

@app.get("/health")
async def health_check():
    try:
        project_count = len([p for p in PROJECTS_DIR.iterdir() if p.is_dir()])
    except Exception:
        project_count = 0
        
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_sessions": count_sessions(),
        "total_projects": project_count
    }

if __name__ == "__main__":
    print("🎬 Starting Story to Image Generator API ...")
    print("📦 Install dependencies: pip install -r requirements.txt")
    print("🔑 Set environment: OPENAI_API_KEY, RUNWARE_API_KEY, TOGETHER_API_KEY")
    print("🌐 Providers: Runware, Together; LLM: Openai")
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)