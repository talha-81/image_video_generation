import json
import requests
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from ..config import PROJECTS_DIR, TIMEOUT
from ..models.schemas import ScenePrompt, GenerationSession

def save_scene_prompts(project_path: Path, scenes: List[ScenePrompt]) -> None:
    """Save scene prompts to a text file for reference."""
    prompts_file = project_path / "scene_prompts.txt"
    content = "Scene Prompts for Image Generation\n" + "=" * 50 + "\n\n"
    
    for scene in scenes:
        content += f"Scene {scene.scene_number}: {scene.scene_title}\n"
        content += f"Script: {scene.script_excerpt}\n"
        content += f"Prompt: {scene.image_prompt}\n"
        content += "-" * 50 + "\n\n"
    
    prompts_file.write_text(content, encoding="utf-8")

def save_approved_images(session: GenerationSession) -> int:
    """Save approved images to the project directory."""
    project_path = PROJECTS_DIR / session.project_id
    images_dir = project_path / "images"
    images_dir.mkdir(exist_ok=True)
    
    saved_count = 0
    
    for preview in session.previews:
        if preview.approved and preview.preview_url:
            try:
                response = requests.get(preview.preview_url, timeout=TIMEOUT)
                response.raise_for_status()
                
                filename = f"scene_{preview.scene_number:03d}.jpg"
                image_path = images_dir / filename
                image_path.write_bytes(response.content)
                saved_count += 1
                
            except requests.exceptions.RequestException as e:
                print(f"Failed to download scene {preview.scene_number}: {e}")
            except Exception as e:
                print(f"Failed to save scene {preview.scene_number}: {e}")
    
    return saved_count

def list_projects() -> Dict:
    """List all projects in the projects directory."""
    projects = []
    
    try:
        for folder in PROJECTS_DIR.iterdir():
            if folder.is_dir():
                analysis_file = folder / "analysis.json"
                if analysis_file.exists():
                    try:
                        analysis = json.loads(analysis_file.read_text(encoding="utf-8"))
                        projects.append({
                            "project_id": folder.name,
                            "created_at": datetime.fromtimestamp(
                                folder.stat().st_ctime
                            ).isoformat(),
                            "analysis": analysis
                        })
                    except Exception as e:
                        print(f"Error loading project {folder.name}: {e}")
    except Exception as e:
        print(f"Error listing projects: {e}")
    
    return {"projects": projects}

def get_project_details(project_id: str) -> Dict:
    """Get detailed information about a specific project."""
    project_path = PROJECTS_DIR / project_id
    if not project_path.exists():
        raise FileNotFoundError("Project not found")

    try:
        # Load script and analysis
        script = (project_path / "script.txt").read_text(encoding="utf-8")
        analysis = json.loads(
            (project_path / "analysis.json").read_text(encoding="utf-8")
        )

        # List generated images
        images_dir = project_path / "images"
        images = []
        if images_dir.exists():
            for img_file in sorted(images_dir.glob("*.jpg")):
                images.append(f"/projects/{project_id}/images/{img_file.name}")

        return {
            "project_id": project_id,
            "script": script,
            "analysis": analysis,
            "images": images,
            "total_images": len(images)
        }
        
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Required project files not found: {e}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid project data: {e}")
    except Exception as e:
        raise Exception(f"Error loading project details: {e}")
