import json
import requests
from typing import List
from ..config import CONFIG, TIMEOUT
from ..models.schemas import ScenePrompt

STYLE_MAP = {
    "cinematic": "cinematic style with dramatic lighting and professional composition, movie-like quality",
    "cartoon": "vibrant cartoon style with bold colors and expressive characters, animated look",
    "realistic": "photorealistic style with natural lighting and detailed textures, real-world appearance",
    "artistic": "artistic illustration style with creative interpretation, painterly quality"
}

def build_prompt(script: str, num_scenes: int, media_type: str) -> str:
    """Build the prompt for AI scene generation."""
    style = STYLE_MAP.get(media_type, "cinematic style")
    
    return f"""
Create {num_scenes} detailed visual scene descriptions from this script.
Style: {style}

Script: {script}

For each distinct scene in the provided story, craft a highly detailed and evocative prompt suitable for an AI image generation model.
This prompt must encapsulate the core narrative moment with vivid sensory details, emotional depth, and atmospheric nuance to ensure a compelling visual representation.
Maintain absolute consistency in character depictions across all scenes: adhere strictly to established physical attributes (such as age, build, hair color and style, facial features, skin tone, and expressions), clothing (including specific garments, colors, fabrics, and wear patterns), and accessories (like jewelry, tools, or props).
Cross-reference descriptions from prior scenes to reinforce continuity, avoiding any deviations that could disrupt the cohesive visual narrative.
Incorporate the story's evolving world and settings with seamless progression: allow environments, lighting conditions (e.g., time of day, weather, or artificial sources), and stylistic elements (e.g., color palette, mood, or artistic influences) to develop organically in alignment with the plot, while upholding a unified overarching aesthetic—such as a consistent art style, composition framing, or visual tone—to evoke a serialized cinematic experience.
Structure each prompt to feel like a sequential frame from a feature film: emphasize dynamic composition, camera angles (e.g., wide shots for establishing scenes, close-ups for intimate moments), focal points, depth of field, and immersive details that build tension, emotion, or progression, ensuring the series of images forms a fluid, interconnected visual storyline rather than isolated snapshots.

Return valid JSON in this exact format:
{{
  "scenes": [
    {{
      "scene_number": 1,
      "scene_title": "Brief scene title (max 50 characters)",
      "script_excerpt": "relevant script text (max 100 characters)",
      "image_prompt": "detailed visual description for image generation in {style} (be very descriptive, include lighting, composition, colors, mood)"
    }}
  ]
}}

Important: Make sure each image_prompt is detailed and includes visual elements like lighting, composition, colors, mood, and style.
""".strip()

def generate_scene_prompts_Openai(
    script: str, 
    num_scenes: int, 
    media_type: str, 
    model: str
) -> List[ScenePrompt]:
    """Generate scene prompts using Openai API."""
    prompt = build_prompt(script, num_scenes, media_type)

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 3000,
    }
    
    headers = {
        "Authorization": f"Bearer {CONFIG['Openai']['api_key']}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            CONFIG["Openai"]["api_url"], 
            headers=headers, 
            json=payload, 
            timeout=TIMEOUT
        )
        response.raise_for_status()
        
        content = response.json()["choices"][0]["message"]["content"]

        # Clean up JSON content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].strip()

        data = json.loads(content)
        return [ScenePrompt(**scene) for scene in data["scenes"]]
        
    except requests.exceptions.RequestException as e:
        print(f"Openai API error: {e}")
        return generate_fallback_scenes(script, num_scenes, media_type)
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Openai response parsing error: {e}")
        return generate_fallback_scenes(script, num_scenes, media_type)
    except Exception as e:
        print(f"Openai unexpected error: {e}")
        return generate_fallback_scenes(script, num_scenes, media_type)

def generate_fallback_scenes(script: str, num_scenes: int, media_type: str) -> List[ScenePrompt]:
    """Generate fallback scenes when AI generation fails."""
    words = script.split()
    words_per_scene = max(1, len(words) // max(num_scenes, 1))

    style_prefixes = {
        "cinematic": "Cinematic shot with dramatic lighting and professional composition showing",
        "cartoon": "Vibrant cartoon style scene with bold colors showing",
        "realistic": "Photorealistic scene with natural lighting showing",
        "artistic": "Artistic illustration with creative interpretation showing"
    }
    style_prefix = style_prefixes.get(media_type, "Scene showing")

    scenes = []
    for i in range(num_scenes):
        start = i * words_per_scene
        end = min((i + 1) * words_per_scene, len(words))
        excerpt = " ".join(words[start:end])
        
        if len(excerpt) > 100:
            excerpt = excerpt[:97] + "..."

        prompt = (f"{style_prefix} {excerpt[:80]}. High quality, detailed, professional "
                 f"rendering with excellent composition and lighting.")
        
        scenes.append(ScenePrompt(
            scene_number=i + 1,
            scene_title=f"Scene {i + 1}",
            script_excerpt=excerpt,
            image_prompt=prompt
        ))
    
    return scenes