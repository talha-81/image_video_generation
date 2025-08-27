"""
Story to Image Generator API Backend

A FastAPI-based service that transforms stories and scripts into AI-generated images.
Features include script analysis, scene prompt generation using OpenRouter LLMs,
and image generation using Runware and Together AI providers.
"""

__version__ = "3.0.0"
__author__ = "Story to Image Generator Team"
__description__ = "Transform stories into images with AI"

from .main import app


from .config import CONFIG, PROJECTS_DIR

__all__ = ['app', 'CONFIG', 'PROJECTS_DIR']