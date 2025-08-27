import time
import uuid
import requests
from typing import Optional
from ..config import CONFIG, TIMEOUT, MAX_RETRIES, RETRY_DELAY
from ..models.schemas import ScenePrompt, PreviewImage

def generate_image_runware(scene: ScenePrompt, model: str) -> Optional[str]:
    """Generate image using Runware API."""
    try:
        payload = {
            "taskType": "imageInference",
            "taskUUID": str(uuid.uuid4()),
            "outputType": "URL",
            "outputFormat": "JPG",
            "positivePrompt": scene.image_prompt,
            "height": 1024,
            "width": 1024,
            "model": model,
            "steps": 25,
            "CFGScale": 7.5,
            "numberResults": 1
        }
        
        headers = {
            "Authorization": f"Bearer {CONFIG['runware']['api_key']}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            CONFIG["runware"]["api_url"], 
            headers=headers, 
            json=[payload], 
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                return data[0].get("imageURL", "")
            elif "data" in data and data["data"]:
                return data["data"][0].get("imageURL", "")
                
    except requests.exceptions.RequestException as e:
        print(f"Runware API request error: {e}")
    except Exception as e:
        print(f"Runware unexpected error: {e}")
    
    return None

def generate_image_together(scene: ScenePrompt, model: str) -> Optional[str]:
    """Generate image using Together AI API."""
    try:
        payload = {
            "model": model,
            "prompt": scene.image_prompt,
            "width": 1024,
            "height": 1024,
            "steps": 4 if "schnell" in model.lower() else 20,
            "n": 1,
            "response_format": "url"
        }
        
        headers = {
            "Authorization": f"Bearer {CONFIG['together']['api_key']}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            CONFIG["together"]["api_url"], 
            headers=headers, 
            json=payload, 
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data and data["data"]:
                return data["data"][0].get("url", "")
                
    except requests.exceptions.RequestException as e:
        print(f"Together AI API request error: {e}")
    except Exception as e:
        print(f"Together AI unexpected error: {e}")
    
    return None

def generate_image_with_retry(scene: ScenePrompt, provider: str, model: str) -> PreviewImage:
    """Generate image with retry logic."""
    start_time = time.time()
    last_error = None
    
    for attempt in range(MAX_RETRIES):
        try:
            if provider == "runware":
                url = generate_image_runware(scene, model)
            elif provider == "together":
                url = generate_image_together(scene, model)
            else:
                url = None
                last_error = f"Unknown provider: {provider}"
            
            if url:
                return PreviewImage(
                    scene_number=scene.scene_number,
                    scene_title=scene.scene_title,
                    prompt=scene.image_prompt,
                    preview_url=url,
                    generation_time=time.time() - start_time,
                    provider_used=provider,
                    model_used=model,
                    approved=False
                )
                
        except Exception as e:
            last_error = str(e)
            print(f"Generation attempt {attempt + 1} failed: {e}")
        
        # Wait before retry (except on last attempt)
        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_DELAY)

    # Return failed preview
    return PreviewImage(
        scene_number=scene.scene_number,
        scene_title=scene.scene_title,
        prompt=scene.image_prompt,
        preview_url="",
        generation_time=time.time() - start_time,
        provider_used=provider,
        model_used=model,
        approved=False,
        error=last_error
    )