# frontend.py
import streamlit as st
import requests
import time
import json
from typing import Dict, Optional, List
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"
POLLING_INTERVAL = 1.5
MAX_POLL_TIME = 300

# Page Configuration
st.set_page_config(
    page_title="Story to Image Generator",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Theme
if "dark_theme" not in st.session_state:
    st.session_state.dark_theme = False

# Dynamic CSS based on theme
def get_theme_css():
    if st.session_state.dark_theme:
        return """
        <style>
        .stApp {
            background-color: #1e1e1e !important;
            color: #ffffff !important;
        }
        
        .main-header {
            background: linear-gradient(135deg, #4a90e2 0%, #7b68ee 50%, #9a4af3 100%);
            color: white;
            padding: 2rem;
            border-radius: 15px;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }
        
        .model-info {
            background: linear-gradient(145deg, #2d2d2d, #3d3d3d);
            color: #ffffff;
            padding: 1rem;
            border-radius: 10px;
            margin: 0.5rem 0;
            border-left: 4px solid #4a90e2;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        }
        
        .success-box {
            background: linear-gradient(145deg, #1e4d3a, #2d5a3d);
            border: 1px solid #28a745;
            color: #90ee90;
            padding: 1.5rem;
            border-radius: 10px;
            margin: 1rem 0;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        }
        
        .error-box {
            background: linear-gradient(145deg, #4d1e1e, #5a2d2d);
            border: 1px solid #dc3545;
            color: #ffcccb;
            padding: 1.5rem;
            border-radius: 10px;
            margin: 1rem 0;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        }
        
        .scene-card {
            border: 1px solid #444444;
            border-radius: 15px;
            padding: 1.5rem;
            margin: 1rem 0;
            background: linear-gradient(145deg, #2d2d2d, #3d3d3d);
            box-shadow: 0 8px 16px rgba(0,0,0,0.3);
            transition: transform 0.3s ease;
            color: #ffffff;
        }
        
        .metric-card {
            background: linear-gradient(145deg, #2d2d2d, #3d3d3d);
            color: #ffffff;
            padding: 1rem;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        }
        
        .failed-scene {
            background: linear-gradient(145deg, #4d1e1e, #5a2d2d);
            border: 2px solid #dc3545;
            border-radius: 10px;
            padding: 1rem;
            margin: 1rem 0;
            color: #ffcccb;
        }
        
        @keyframes loading-spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .loading-spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255,255,255,.3);
            border-radius: 50%;
            border-top-color: #4a90e2;
            animation: loading-spin 1s ease-in-out infinite;
            margin-right: 10px;
        }
        </style>
        """
    else:
        return """
        <style>
        .main-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            color: white;
            padding: 2rem;
            border-radius: 15px;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }

        .main-header h1 {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .model-info {
            background: linear-gradient(145deg, #f8f9fa, #e9ecef);
            padding: 1rem;
            border-radius: 10px;
            margin: 0.5rem 0;
            border-left: 4px solid #667eea;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }

        .success-box {
            background: linear-gradient(145deg, #d4edda, #c3e6cb);
            border: 1px solid #28a745;
            color: #155724;
            padding: 1.5rem;
            border-radius: 10px;
            margin: 1rem 0;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }

        .error-box {
            background: linear-gradient(145deg, #f8d7da, #f5c6cb);
            border: 1px solid #dc3545;
            color: #721c24;
            padding: 1.5rem;
            border-radius: 10px;
            margin: 1rem 0;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }

        .status-generating {
            color: #856404;
            background: linear-gradient(145deg, #fff3cd, #ffeaa7);
            padding: 1rem;
            border-radius: 10px;
            border-left: 4px solid #ffc107;
            animation: pulse 2s infinite;
        }

        .status-complete {
            color: #155724;
            background: linear-gradient(145deg, #d4edda, #c3e6cb);
            padding: 1rem;
            border-radius: 10px;
            border-left: 4px solid #28a745;
        }

        .scene-card {
            border: 1px solid #dee2e6;
            border-radius: 15px;
            padding: 1.5rem;
            margin: 1rem 0;
            background: linear-gradient(145deg, #ffffff, #f8f9fa);
            box-shadow: 0 8px 16px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }

        .scene-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 24px rgba(0,0,0,0.15);
        }

        .metric-card {
            background: linear-gradient(145deg, #ffffff, #f8f9fa);
            padding: 1rem;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }

        .failed-scene {
            background: linear-gradient(145deg, #f8d7da, #f5c6cb);
            border: 2px solid #dc3545;
            border-radius: 10px;
            padding: 1rem;
            margin: 1rem 0;
            color: #721c24;
        }

        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.7; }
            100% { opacity: 1; }
        }

        @keyframes loading-spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .loading-spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(102,126,234,.3);
            border-radius: 50%;
            border-top-color: #667eea;
            animation: loading-spin 1s ease-in-out infinite;
            margin-right: 10px;
        }

        .stButton > button {
            background: linear-gradient(145deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 10px;
            padding: 0.7rem 1.5rem;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }

        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.3);
        }
        </style>
        """

st.markdown(get_theme_css(), unsafe_allow_html=True)

# Helper Functions
@st.cache_data(ttl=60)
def check_backend_health() -> Dict:
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            return {"healthy": True, "data": response.json()}
        return {"healthy": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"healthy": False, "error": str(e)}

@st.cache_data(ttl=300)
def load_models() -> Optional[Dict]:
    try:
        response = requests.get(f"{API_BASE_URL}/models", timeout=30)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None

def analyze_script(script: str, title: str) -> Optional[Dict]:
    try:
        data = {"script": script, "title": title}
        response = requests.post(f"{API_BASE_URL}/analyze-script", json=data, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Analysis failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Error analyzing script: {str(e)}")
        return None

def start_generation(payload: Dict) -> Optional[Dict]:
    try:
        response = requests.post(f"{API_BASE_URL}/generate-previews", json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Generation failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Error starting generation: {str(e)}")
        return None

def get_generation_status(session_id: str) -> Optional[Dict]:
    try:
        response = requests.get(f"{API_BASE_URL}/generation-status/{session_id}", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None

def approve_previews(session_id: str, approvals: Dict[str, bool]) -> Optional[Dict]:
    try:
        payload = {"session_id": session_id, "scene_approvals": approvals}
        response = requests.post(f"{API_BASE_URL}/approve-previews", json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Approval failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Error submitting approvals: {str(e)}")
        return None

def regenerate_scene(session_id: str, scene_number: int, image_provider: str, image_model: str) -> Optional[Dict]:
    try:
        payload = {
            "session_id": session_id,
            "scene_number": scene_number,
            "image_provider": image_provider,
            "image_model": image_model
        }
        response = requests.post(f"{API_BASE_URL}/regenerate-scene", json=payload, timeout=60)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Regeneration failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Error regenerating scene: {str(e)}")
        return None

@st.cache_data(ttl=30)
def load_projects() -> Optional[Dict]:
    try:
        response = requests.get(f"{API_BASE_URL}/projects", timeout=30)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None

# Initialize Session State
if "available_models" not in st.session_state:
    with st.spinner("Loading models..."):
        placeholder = st.empty()
        placeholder.markdown("""
        <div style="text-align: center; padding: 2rem;">
            <div class="loading-spinner"></div>
            <p>Loading AI models and configurations...</p>
        </div>
        """, unsafe_allow_html=True)
        st.session_state.available_models = load_models()
        placeholder.empty()

if "current_project" not in st.session_state:
    st.session_state.current_project = None

if "current_session" not in st.session_state:
    st.session_state.current_session = None

if "current_page" not in st.session_state:
    st.session_state.current_page = "Create Story"

if "navigation_history" not in st.session_state:
    st.session_state.navigation_history = ["Create Story"]

if "project_created" not in st.session_state:
    st.session_state.project_created = False

if "project_creation_result" not in st.session_state:
    st.session_state.project_creation_result = None

# Navigation Functions
def navigate_to(page: str, delay: float = 0.5):
    if page != st.session_state.current_page:
        st.session_state.navigation_history.append(st.session_state.current_page)
        st.session_state.current_page = page
        if delay > 0:
            time.sleep(delay)
        st.rerun()

def go_back():
    if len(st.session_state.navigation_history) > 1:
        st.session_state.navigation_history.pop()
        st.session_state.current_page = st.session_state.navigation_history[-1]
        st.rerun()

# Main Header
st.markdown("""
<div class="main-header">
    <h1>Story to Image Generator</h1>
    <p>Transform your stories into stunning AI-generated images using cutting-edge AI technology</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("Navigation")
    
    # Theme toggle button
    theme_icon = "🌙" if not st.session_state.dark_theme else "☀️"
    theme_text = "Dark Mode" if not st.session_state.dark_theme else "Light Mode"
    
    if st.button(f"{theme_icon} {theme_text}", key="theme_toggle"):
        st.session_state.dark_theme = not st.session_state.dark_theme
        st.rerun()
    
    # Backend health check
    health = check_backend_health()
    if health["healthy"]:
        st.success("Backend Online")
        if "data" in health:
            data = health["data"]
            st.caption(f"Active sessions: {data.get('active_sessions', 0)}")
            st.caption(f"Total projects: {data.get('total_projects', 0)}")
    else:
        st.error(f"Backend Offline: {health['error']}")
        st.error("Please start the backend server first!")
        st.stop()
    
    # Navigation with current page highlighting
    pages = [
        "Create Story",
        "Generate Images", 
        "Monitor Progress",
        "My Projects"
    ]
    
    current_page = st.session_state.current_page
    page = st.radio("Go to:", pages, index=pages.index(current_page) if current_page in pages else 0)
    
    if page != st.session_state.current_page:
        navigate_to(page, delay=0.3)
    
    # Back button
    if len(st.session_state.navigation_history) > 1:
        if st.button("Go Back"):
            go_back()
    
    # Current project info
    if st.session_state.current_project:
        st.markdown("---")
        st.markdown("### Current Project")
        project = st.session_state.current_project
        st.info(f"**ID:** {project['project_id'][:15]}...\n\n**Words:** {project['analysis']['word_count']}")
    
    # Current session info
    if st.session_state.current_session:
        st.markdown("### Active Session")
        st.info(f"**ID:** {st.session_state.current_session[:15]}...")

# Page: Create Story
def create_story_page():
    st.header("Create New Story Project")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.form("script_form", clear_on_submit=False):
            title = st.text_input(
                "Project Title*", 
                placeholder="Enter a descriptive title for your story",
                help="Give your project a memorable name"
            )
            
            script = st.text_area(
                "Story Script*", 
                height=300,
                placeholder="Enter your story or script here...\n\nTip: The more detailed and descriptive your story, the better the AI-generated images will be!",
                help="Paste or write your story content. Longer scripts generate more detailed scenes."
            )
            
            col_form1, col_form2 = st.columns(2)
            with col_form1:
                submitted = st.form_submit_button("Analyze Script & Create Project", use_container_width=True)
            
            with col_form2:
                clear_form = st.form_submit_button("Clear Form", use_container_width=True)
            
            if clear_form:
                st.rerun()
                
            if submitted:
                if not title.strip():
                    st.error("Please provide a project title")
                    return
                    
                if not script.strip():
                    st.error("Please provide a story script")
                    return
                
                if len(script.split()) < 10:
                    st.error("Script too short. Please provide at least 10 words for analysis.")
                    return
                
                with st.spinner("Analyzing script and creating project..."):
                    result = analyze_script(script.strip(), title.strip())
                
                if result:
                    st.session_state.current_project = result
                    st.session_state.project_created = True
                    st.session_state.project_creation_result = result
                    
                    st.markdown(f"""
                    <div class="success-box">
                        <h3>Project Created Successfully!</h3>
                        <p><strong>Project ID:</strong> {result['project_id']}</p>
                        <p><strong>Word Count:</strong> {result['analysis']['word_count']} words</p>
                        <p><strong>Recommended Scenes:</strong> {result['analysis']['recommended_scenes']} scenes</p>
                        <p><strong>Estimated Duration:</strong> {result['analysis']['estimated_duration_minutes']:.1f} minutes</p>
                        <p><strong>Complexity:</strong> {result['analysis']['complexity_score']}</p>
                    </div>
                    """, unsafe_allow_html=True)

                    
                    navigate_to("Generate Images", delay=1.0)
    
    with col2:
        st.markdown("### Tips for Better Results")
        st.info("""
        **Writing Tips:**
        • Use descriptive language with visual details
        • Include character descriptions and settings
        • Break your story into clear scenes
        • Mention colors, lighting, and mood
        
        **Script Length Guide:**
        • **Short (50-100 words):** 2-3 scenes
        • **Medium (100-500 words):** 4-6 scenes  
        • **Long (500+ words):** 6-10 scenes
        
        **Style Recommendations:**
        • **Cinematic:** Movie-like dramatic scenes
        • **Cartoon:** Animated, colorful style
        • **Realistic:** Photo-realistic images
        • **Artistic:** Creative interpretation
        """)
        
        if st.session_state.available_models:
            models = st.session_state.available_models
            st.markdown("### Available AI Models")
            
            ai_models = models.get("ai_models", {}).get("openrouter", [])
            image_models = models.get("image_models", {})
            runware_count = len(image_models.get("runware", []))
            together_count = len(image_models.get("together", []))
            
            st.success(f"**AI Models:** {len(ai_models)} available")
            st.success(f"**Image Models:** {runware_count + together_count} available")

# Page: Generate Images
def generate_images_page():
    st.header("Generate Images from Story")
    
    # Show project creation success message if just created
    if st.session_state.project_creation_result:
        result = st.session_state.project_creation_result
        st.markdown(f"""
        <div class="success-box">
            <h3>Project Ready for Image Generation!</h3>
            <p><strong>Project ID:</strong> {result['project_id']}</p>
            <p><strong>Word Count:</strong> {result['analysis']['word_count']} words</p>
            <p><strong>Recommended Scenes:</strong> {result['analysis']['recommended_scenes']} scenes</p>
            <p><strong>Estimated Duration:</strong> {result['analysis']['estimated_duration_minutes']:.1f} minutes</p>
            <p><strong>Complexity:</strong> {result['analysis']['complexity_score']}</p>
        </div>
        """, unsafe_allow_html=True) # Clear after showing
    
    # Project selection
    if not st.session_state.current_project:
        st.warning("No project selected. Please create a project first or select from existing projects.")
        
        projects = load_projects()
        if projects and "projects" in projects and projects["projects"]:
            st.markdown("### Select from Existing Projects")
            
            for project in projects["projects"][:5]:
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"**{project['project_id']}**")
                    st.caption(f"Words: {project['analysis'].get('word_count', 0)} | "
                             f"Scenes: {project['analysis'].get('recommended_scenes', 0)}")
                
                with col2:
                    if st.button("Select", key=f"select_{project['project_id']}"):
                        st.session_state.current_project = project
                        st.success(f"Selected: {project['project_id']}")
                        st.rerun()
                
                with col3:
                    if st.button("View", key=f"view_{project['project_id']}"):
                        navigate_to("My Projects")
        
        # Manual project ID entry
        with st.expander("Advanced: Enter Project ID Manually"):
            manual_project_id = st.text_input(
                "Project ID:", 
                placeholder="story_20241201_123456",
                help="Enter the exact project ID if you know it"
            )
            
            if manual_project_id and st.button("Load Project"):
                try:
                    response = requests.get(f"{API_BASE_URL}/projects/{manual_project_id}", timeout=30)
                    if response.status_code == 200:
                        project_data = response.json()
                        st.session_state.current_project = {
                            "project_id": manual_project_id,
                            "analysis": {"word_count": len(project_data["script"].split())}
                        }
                        st.success(f"Loaded project: {manual_project_id}")
                        st.rerun()
                    else:
                        st.error(f"Project not found: {manual_project_id}")
                except Exception as e:
                    st.error(f"Error loading project: {str(e)}")
        
        return
    
    # Show current project
    project = st.session_state.current_project
    st.success(f"**Current Project:** {project['project_id']} ({project['analysis']['word_count']} words)")
    
    # Model selection
    models = st.session_state.available_models
    if not models:
        st.error("Failed to load available models. Please check backend connection.")
        return
    
    st.markdown("### Generation Settings")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### AI Scene Analysis")
        
        ai_models = models.get("ai_models", {}).get("openrouter", [])
        if ai_models:
            ai_model = st.selectbox("AI Model:", ai_models, help="Choose AI model for scene analysis")
            
            model_descriptions = {
                "openai/gpt-oss-20b:free": "Fast and efficient for scene analysis",
                "meta-llama/llama-3.1-8b-instruct:free": "Creative and detailed descriptions",
                "microsoft/phi-3-mini-128k-instruct:free": "Balanced performance and creativity"
            }
            
            if ai_model in model_descriptions:
                st.info(model_descriptions[ai_model])
        else:
            st.warning("No AI models available, using fallback")
            ai_model = "fallback"
    
    with col2:
        st.markdown("#### Image Generation")
        
        image_provider = st.selectbox("Image Provider:", ["runware", "together"])
        
        if image_provider == "runware":
            runware_models = models.get("image_models", {}).get("runware", [])
            if runware_models:
                image_model = st.selectbox("Runware Model:", runware_models)
                st.info("High-quality, fast generation")
            else:
                st.error("No Runware models available")
                return
        else:
            together_models = models.get("image_models", {}).get("together", [])
            if together_models:
                image_model = st.selectbox("Together Model:", together_models)
                st.info("Diverse model options")
            else:
                st.error("No Together AI models available")
                return
    
    with col3:
        st.markdown("#### Scene Settings")
        
        num_scenes = st.number_input(
            "Number of scenes:", 
            min_value=1, 
            max_value=10, 
            value=min(project['analysis'].get('recommended_scenes', 4), 8),
            help="More scenes = more detailed story breakdown"
        )
        
        media_type = st.selectbox("Visual Style:", [
            "cinematic", "cartoon", "realistic", "artistic"
        ], help="Choose the visual style for your images")
    
    # Style preview
    style_descriptions = {
        "cinematic": "**Cinematic:** Movie-like with dramatic lighting and professional composition",
        "cartoon": "**Cartoon:** Vibrant animated style with bold colors and expressive characters", 
        "realistic": "**Realistic:** Photorealistic appearance with natural lighting and detailed textures",
        "artistic": "**Artistic:** Creative artistic interpretation with painterly quality"
    }
    
    st.markdown(f"**Selected Style:** {style_descriptions.get(media_type, 'Custom style selected')}")
    
    # Navigation buttons
    col_nav1, col_nav2, col_nav3 = st.columns(3)
    
    with col_nav1:
        if st.button("Back to Create Story", use_container_width=True):
            navigate_to("Create Story")
    
    with col_nav2:
        if st.button("Clear Project", use_container_width=True):
            st.session_state.current_project = None
            st.rerun()
    
    with col_nav3:
        generate_clicked = st.button("Generate Scene Previews", use_container_width=True, type="primary")
    
    if generate_clicked:
        payload = {
            "project_id": project['project_id'],
            "num_scenes": num_scenes,
            "media_type": media_type,
            "ai_provider": "openrouter",
            "ai_model": ai_model,
            "image_provider": image_provider,
            "image_model": image_model,
        }
        
        with st.spinner("Starting generation process..."):
            result = start_generation(payload)
        
        if result:
            st.session_state.current_session = result["session_id"]
            
            st.markdown(f"""
            <div class="success-box">
                <h3>Generation Started Successfully!</h3>
                <p><strong>Session ID:</strong> {result['session_id']}</p>
                <p><strong>Total Scenes:</strong> {result['total_scenes']}</p>
                <p><strong>Status:</strong> {result['status'].title()}</p>
            </div>
            """, unsafe_allow_html=True)
            
            
            navigate_to("Monitor Progress", delay=1.0)

# Page: Monitor Progress
def monitor_progress_page():
    st.header("Monitor Generation Progress")
    
    # Session selection
    if st.session_state.current_session:
        session_id = st.text_input(
            "Session ID:", 
            value=st.session_state.current_session,
            help="Current active session"
        )
    else:
        session_id = st.text_input(
            "Session ID:", 
            placeholder="session_abcd1234",
            help="Enter session ID to monitor"
        )
    
    if not session_id:
        st.info("Enter a session ID to monitor progress")
        
        if st.button("Back to Generate Images"):
            navigate_to("Generate Images")
        return
    
    # Control buttons
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        auto_refresh = st.checkbox("Auto-refresh", value=True, help="Automatically update every 1.5 seconds")
    
    with col2:
        manual_refresh = st.button("Check Status", help="Manually check current status")
    
    with col3:
        if st.button("Back to Generate"):
            navigate_to("Generate Images")
    
    with col4:
        if st.button("Clear Session"):
            st.session_state.current_session = None
            st.rerun()
    
    if manual_refresh or auto_refresh:
        status = get_generation_status(session_id)
        
        if not status:
            st.error("Session not found or expired")
            if st.button("Try Different Session"):
                st.session_state.current_session = None
                st.rerun()
            return
        
        # Progress display
        progress = status["completed_scenes"] / max(status["total_scenes"], 1)
        st.progress(progress, text=f"Progress: {status['completed_scenes']}/{status['total_scenes']} scenes")
        
        # Status metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            status_color = {"generating": "🟡", "previewing": "🔵", "completed": "🟢", "failed": "🔴"}
            st.markdown(f"""
            <div class="metric-card">
                <h3>{status_color.get(status['status'], '⚪')} Status</h3>
                <p><strong>{status['status'].title()}</strong></p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <h3>Progress</h3>
                <p><strong>{status['completed_scenes']}/{status['total_scenes']}</strong></p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <h3>Total Scenes</h3>
                <p><strong>{status['total_scenes']}</strong></p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            error_count = len(status.get("errors", []))
            error_color = "🔴" if error_count > 0 else "🟢"
            st.markdown(f"""
            <div class="metric-card">
                <h3>{error_color} Errors</h3>
                <p><strong>{error_count}</strong></p>
            </div>
            """, unsafe_allow_html=True)
        
        # Show errors if any
        if status.get("errors"):
            with st.expander(f"View Errors ({len(status['errors'])})", expanded=True):
                for i, error in enumerate(status["errors"], 1):
                    st.error(f"**Error {i}:** {error}")
        
        # Show generation status
        if status["status"] == "generating":
            st.markdown("""
            <div class="status-generating">
                <h3>Generation In Progress</h3>
                <p>AI is creating your scene images. This may take several minutes depending on the number of scenes and model complexity.</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Show previews
        if status["previews"]:
            st.markdown("---")
            st.subheader("Generated Previews")
            
            # Approval section for completed generation
            if status["status"] in ["previewing", "completed"]:
                
                # Display previews in a grid
                cols = st.columns(min(3, len(status["previews"])))
                approvals = {}
                regenerate_requests = {}
                
                for i, preview in enumerate(status["previews"]):
                    with cols[i % 3]:
                        st.markdown(f"""
                        <div class="scene-card">
                            <h4>Scene {preview['scene_number']}: {preview['scene_title']}</h4>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if preview["preview_url"]:
                            st.image(preview["preview_url"], use_container_width=True)
                            
                            # Approval checkbox
                            approvals[str(preview["scene_number"])] = st.checkbox(
                                f"Save Scene {preview['scene_number']}", 
                                value=True,
                                key=f"approve_{preview['scene_number']}_{session_id}",
                                help="Check to include this scene in final output"
                            )
                            
                            # Regenerate button
                            if st.button(
                                "Regenerate", 
                                key=f"regen_{preview['scene_number']}_{session_id}",
                                help="Generate a new version of this scene",
                                use_container_width=True
                            ):
                                regenerate_requests[preview["scene_number"]] = {
                                    "provider": preview["provider_used"],
                                    "model": preview["model_used"]
                                }
                            
                            # Scene details
                            with st.expander(f"Scene {preview['scene_number']} Details"):
                                st.text_area(
                                    "Image Prompt:", 
                                    preview['prompt'], 
                                    height=100, 
                                    disabled=True,
                                    key=f"prompt_{preview['scene_number']}_{session_id}"
                                )
                                st.caption(f"Generation time: {preview['generation_time']:.1f}s")
                                st.caption(f"Provider: {preview['provider_used']}")
                                st.caption(f"Model: {preview['model_used']}")
                                
                                if preview.get('error'):
                                    st.error(f"Error: {preview['error']}")
                        else:
                            # Failed scene with regeneration option
                            st.markdown(f"""
                            <div class="failed-scene">
                                <h4>Generation Failed</h4>
                                <p><strong>Scene {preview['scene_number']}:</strong> {preview['scene_title']}</p>
                                <p><strong>Error:</strong> {preview.get('error', 'Unknown error occurred')}</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Regenerate button for failed scenes
                            col_regen1, col_regen2 = st.columns(2)
                            
                            with col_regen1:
                                if st.button(
                                    f"Retry Scene {preview['scene_number']}", 
                                    key=f"retry_{preview['scene_number']}_{session_id}",
                                    help="Try generating this scene again",
                                    use_container_width=True
                                ):
                                    regenerate_requests[preview["scene_number"]] = {
                                        "provider": preview["provider_used"],
                                        "model": preview["model_used"]
                                    }
                            
                            with col_regen2:
                                # Option to try different provider
                                alt_provider = "together" if preview["provider_used"] == "runware" else "runware"
                                if st.button(
                                    f"Try {alt_provider.title()}", 
                                    key=f"alt_{preview['scene_number']}_{session_id}",
                                    help=f"Try generating with {alt_provider} instead",
                                    use_container_width=True
                                ):
                                    # Get alternative model
                                    models = st.session_state.available_models
                                    alt_models = models.get("image_models", {}).get(alt_provider, [])
                                    if alt_models:
                                        regenerate_requests[preview["scene_number"]] = {
                                            "provider": alt_provider,
                                            "model": alt_models[0]
                                        }
                            
                            approvals[str(preview["scene_number"])] = False
                
                # Handle regeneration requests
                for scene_num, regen_info in regenerate_requests.items():
                    with st.spinner(f"Regenerating scene {scene_num}..."):
                        regen_result = regenerate_scene(
                            session_id, 
                            scene_num,
                            regen_info["provider"],
                            regen_info["model"]
                        )
                    
                    if regen_result and regen_result.get("status") == "success":
                        st.success(f"Scene {scene_num} regenerated successfully!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"Failed to regenerate scene {scene_num}")
                
                # Approval form
                st.markdown("---")
                st.markdown("### Save Selected Scenes")
                
                selected_count = sum(1 for approved in approvals.values() if approved)
                
                if selected_count == 0:
                    st.warning("No scenes selected for saving. Please select at least one scene.")
                else:
                    st.info(f"**{selected_count}** out of **{len(status['previews'])}** scenes selected for saving")
                
                col_save1, col_save2 = st.columns(2)
                
                with col_save1:
                    if st.button("Save Selected Scenes", disabled=selected_count == 0, use_container_width=True, type="primary"):
                        with st.spinner("Saving approved scenes..."):
                            result = approve_previews(session_id, approvals)
                        
                        if result:
                            st.markdown(f"""
                            <div class="success-box">
                                <h3>Scenes Saved Successfully!</h3>
                                <p><strong>Saved Images:</strong> {result['saved_images']}</p>
                                <p><strong>Total Scenes:</strong> {result['total_scenes']}</p>
                                <p>Your images are now saved in the project folder!</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            
                            navigate_to("My Projects", delay=1.5)
                
                with col_save2:
                    if st.button("Select All", use_container_width=True):
                        st.rerun()
        
        # Auto-refresh logic
        if auto_refresh and status["status"] == "generating":
            time.sleep(1.5)
            st.rerun()

# Page: My Projects
def my_projects_page():
    st.header("My Projects")
    
    projects = load_projects()
    
    if not projects or not projects.get("projects"):
        st.info("No projects found. Create your first project!")
        
        if st.button("Create New Project", use_container_width=True, type="primary"):
            navigate_to("Create Story", delay=0.3)
        return
    
    project_list = projects["projects"]
    st.success(f"Found **{len(project_list)}** projects")
    
    # Search and filter
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_term = st.text_input("Search projects:", placeholder="Enter project ID or keyword")
    
    with col2:
        sort_by = st.selectbox("Sort by:", ["Newest First", "Oldest First", "Most Words", "Least Words"])
    
    # Filter and sort projects
    filtered_projects = project_list
    
    if search_term:
        filtered_projects = [
            p for p in project_list 
            if search_term.lower() in p['project_id'].lower()
        ]
    
    # Sort projects
    if sort_by == "Newest First":
        filtered_projects = sorted(filtered_projects, key=lambda x: x['created_at'], reverse=True)
    elif sort_by == "Oldest First":
        filtered_projects = sorted(filtered_projects, key=lambda x: x['created_at'])
    elif sort_by == "Most Words":
        filtered_projects = sorted(filtered_projects, key=lambda x: x['analysis'].get('word_count', 0), reverse=True)
    elif sort_by == "Least Words":
        filtered_projects = sorted(filtered_projects, key=lambda x: x['analysis'].get('word_count', 0))
    
    st.markdown(f"Showing **{len(filtered_projects)}** projects")
    
    # Display projects
    for i, project in enumerate(filtered_projects):
        with st.expander(
            f"**{project['project_id']}** - {project['analysis'].get('word_count', 0)} words",
            expanded=(i < 3)
        ):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Project details
                created_date = project['created_at'][:19].replace('T', ' ')
                
                st.markdown(f"""
                **Created:** {created_date}  
                **Word Count:** {project['analysis'].get('word_count', 'N/A')} words  
                **Recommended Scenes:** {project['analysis'].get('recommended_scenes', 'N/A')} scenes  
                **Est. Duration:** {project['analysis'].get('estimated_duration_minutes', 'N/A')} minutes  
                **Complexity:** {project['analysis'].get('complexity_score', 'N/A')}  
                """)
                
                # Try to load project details to show images
                try:
                    response = requests.get(f"{API_BASE_URL}/projects/{project['project_id']}", timeout=10)
                    if response.status_code == 200:
                        details = response.json()
                        if details.get('images'):
                            st.success(f"**{len(details['images'])} images generated**")
                            
                            # Show thumbnail gallery
                            if len(details['images']) > 0:
                                st.markdown("**Generated Images:**")
                                img_cols = st.columns(min(4, len(details['images'])))
                                
                                for idx, img_path in enumerate(details['images'][:4]):
                                    with img_cols[idx]:
                                        try:
                                            img_url = f"{API_BASE_URL}{img_path}"
                                            st.image(img_url, use_container_width=True, caption=f"Scene {idx+1}")
                                        except:
                                            st.error("Image load failed")
                                
                                if len(details['images']) > 4:
                                    st.caption(f"... and {len(details['images']) - 4} more images")
                        else:
                            st.info("No images generated yet")
                except:
                    st.warning("Could not load project details")
            
            with col2:
                st.markdown("### Actions")
                
                # Action buttons
                if st.button("Generate Images", key=f"gen_{project['project_id']}", use_container_width=True):
                    st.session_state.current_project = project
                    navigate_to("Generate Images", delay=0.3)
                
                if st.button("Use Project", key=f"use_{project['project_id']}", use_container_width=True):
                    st.session_state.current_project = project
                    st.success(f"Selected: {project['project_id']}")
                    time.sleep(0.5)
                    st.rerun()
                
                if st.button("View Details", key=f"view_{project['project_id']}", use_container_width=True):
                    # Show detailed project information
                    try:
                        response = requests.get(f"{API_BASE_URL}/projects/{project['project_id']}", timeout=10)
                        if response.status_code == 200:
                            details = response.json()
                            
                            # Show in modal-like expander
                            with st.expander(f"Full Details - {project['project_id']}", expanded=True):
                                st.markdown("### Original Script")
                                st.text_area("Script Content:", details['script'], height=200, disabled=True)
                                
                                if details.get('images'):
                                    st.markdown("### All Generated Images")
                                    
                                    # Display all images in a grid
                                    img_cols = st.columns(3)
                                    for idx, img_path in enumerate(details['images']):
                                        with img_cols[idx % 3]:
                                            try:
                                                img_url = f"{API_BASE_URL}{img_path}"
                                                st.image(img_url, use_container_width=True, caption=f"Scene {idx+1}")
                                            except:
                                                st.error(f"Could not load image {idx+1}")
                    except Exception as e:
                        st.error(f"Error loading project details: {str(e)}")

# Main Navigation Router
current_page = st.session_state.current_page

if current_page == "Create Story":
    create_story_page()
elif current_page == "Generate Images":
    generate_images_page()
elif current_page == "Monitor Progress":
    monitor_progress_page()
elif current_page == "My Projects":
    my_projects_page()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem; background: linear-gradient(145deg, #f8f9fa, #e9ecef); border-radius: 10px; margin-top: 2rem;">
    <h4>Story to Image Generator v3.0</h4>
    <p>Powered by <strong>OpenRouter</strong>, <strong>Runware</strong> & <strong>Together AI</strong></p>
    <p style="font-size: 0.9em; color: #888;">Transform your stories into stunning AI-generated images with cutting-edge technology</p>
</div>
""", unsafe_allow_html=True)

# Debug Information (only show in development)
if st.checkbox("Debug Mode", value=False):
    st.markdown("---")
    st.markdown("### Debug Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.json({
            "current_page": st.session_state.current_page,
            "navigation_history": st.session_state.navigation_history[-3:],
            "has_current_project": st.session_state.current_project is not None,
            "has_current_session": st.session_state.current_session is not None,
        })
    
    with col2:
        if st.session_state.current_project:
            st.json({
                "project_id": st.session_state.current_project.get("project_id"),
                "word_count": st.session_state.current_project.get("analysis", {}).get("word_count"),
                "recommended_scenes": st.session_state.current_project.get("analysis", {}).get("recommended_scenes")
            })
        
        if st.session_state.current_session:
            st.text(f"Session: {st.session_state.current_session}")
    
    # Clear session state button
    if st.button("Clear All Session Data", type="secondary"):
        for key in ["current_project", "current_session", "navigation_history"]:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state.current_page = "Create Story"
        st.rerun()