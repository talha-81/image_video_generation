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

# Enhanced CSS with improved styling
def get_theme_css():
    if st.session_state.dark_theme:
        return """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        .stApp {
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%) !important;
            color: #ffffff !important;
            font-family: 'Inter', sans-serif !important;
        }
        
        .main-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 25%, #f093fb 50%, #f5576c 75%, #4facfe 100%);
            color: white;
            padding: 3rem 2rem;
            border-radius: 20px;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 20px 40px rgba(102,126,234,0.3), 0 0 0 1px rgba(255,255,255,0.1);
            position: relative;
            overflow: hidden;
        }
        
        .main-header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.1) 50%, transparent 70%);
            animation: shimmer 3s infinite;
        }
        
        .main-header h1 {
            font-size: 3rem !important;
            font-weight: 700 !important;
            margin-bottom: 0.5rem !important;
            text-shadow: 2px 2px 8px rgba(0,0,0,0.3);
            z-index: 2;
            position: relative;
        }
        
        .main-header p {
            font-size: 1.2rem !important;
            font-weight: 300 !important;
            opacity: 0.9;
            z-index: 2;
            position: relative;
        }
        
        @keyframes shimmer {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }
        
        .nav-button {
            background: linear-gradient(145deg, #2d3748, #4a5568) !important;
            color: #ffffff !important;
            border: 1px solid #4a5568 !important;
            border-radius: 12px !important;
            padding: 0.8rem 1.5rem !important;
            font-weight: 600 !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
            backdrop-filter: blur(10px) !important;
            margin: 0.2rem 0 !important;
        }
        
        .nav-button:hover {
            background: linear-gradient(145deg, #4a5568, #667eea) !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 25px rgba(102,126,234,0.4) !important;
        }
        
        .nav-button.active {
            background: linear-gradient(145deg, #667eea, #764ba2) !important;
            box-shadow: 0 0 20px rgba(102,126,234,0.5) !important;
        }
        
        .model-info {
            background: linear-gradient(145deg, #2d3748, #3d4852);
            color: #ffffff;
            padding: 1.5rem;
            border-radius: 15px;
            margin: 1rem 0;
            border-left: 4px solid #667eea;
            box-shadow: 0 8px 20px rgba(0,0,0,0.3);
            backdrop-filter: blur(10px);
        }
        
        .success-box {
            background: linear-gradient(145deg, rgba(72,187,120,0.2), rgba(72,187,120,0.1));
            border: 1px solid #48bb78;
            color: #68d391;
            padding: 2rem;
            border-radius: 15px;
            margin: 1rem 0;
            box-shadow: 0 8px 20px rgba(72,187,120,0.2);
            backdrop-filter: blur(10px);
        }
        
        .error-box {
            background: linear-gradient(145deg, rgba(245,101,101,0.2), rgba(245,101,101,0.1));
            border: 1px solid #f56565;
            color: #fc8181;
            padding: 2rem;
            border-radius: 15px;
            margin: 1rem 0;
            box-shadow: 0 8px 20px rgba(245,101,101,0.2);
            backdrop-filter: blur(10px);
        }
        
        .scene-card {
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 20px;
            padding: 2rem;
            margin: 1.5rem 0;
            background: linear-gradient(145deg, rgba(45,55,72,0.8), rgba(61,72,82,0.6));
            box-shadow: 0 12px 30px rgba(0,0,0,0.4);
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            color: #ffffff;
            backdrop-filter: blur(15px);
        }
        
        .scene-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.5);
            border-color: rgba(102,126,234,0.3);
        }
        
        .metric-card {
            background: linear-gradient(145deg, rgba(45,55,72,0.8), rgba(61,72,82,0.6));
            color: #ffffff;
            padding: 1.5rem;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 8px 20px rgba(0,0,0,0.3);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        .custom-button {
            background: linear-gradient(145deg, #667eea, #764ba2) !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 0.8rem 2rem !important;
            font-weight: 600 !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 6px 15px rgba(102,126,234,0.4) !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
        }
        
        .custom-button:hover {
            transform: translateY(-3px) !important;
            box-shadow: 0 10px 25px rgba(102,126,234,0.6) !important;
            background: linear-gradient(145deg, #764ba2, #667eea) !important;
        }
        
        .custom-button:active {
            transform: translateY(-1px) !important;
        }
        
        .primary-button {
            background: linear-gradient(145deg, #f093fb, #f5576c) !important;
            box-shadow: 0 6px 15px rgba(245,87,108,0.4) !important;
        }
        
        .primary-button:hover {
            box-shadow: 0 10px 25px rgba(245,87,108,0.6) !important;
        }
        
        .loading-spinner {
            display: inline-block;
            width: 24px;
            height: 24px;
            border: 3px solid rgba(255,255,255,.2);
            border-radius: 50%;
            border-top-color: #667eea;
            animation: loading-spin 1s ease-in-out infinite;
            margin-right: 12px;
        }
        
        @keyframes loading-spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .stSelectbox > div > div {
            background: rgba(45,55,72,0.8) !important;
            border: 1px solid rgba(255,255,255,0.2) !important;
            border-radius: 10px !important;
        }
        
        .stTextInput > div > div > input {
            background: rgba(45,55,72,0.8) !important;
            border: 1px solid rgba(255,255,255,0.2) !important;
            border-radius: 10px !important;
            color: white !important;
        }
        
        .stTextArea > div > div > textarea {
            background: rgba(45,55,72,0.8) !important;
            border: 1px solid rgba(255,255,255,0.2) !important;
            border-radius: 10px !important;
            color: white !important;
        }
        
        .stNumberInput > div > div > input {
            background: rgba(45,55,72,0.8) !important;
            border: 1px solid rgba(255,255,255,0.2) !important;
            border-radius: 10px !important;
            color: white !important;
        }
        
        .sidebar .nav-button {
            width: 100% !important;
            margin-bottom: 0.5rem !important;
            text-align: center !important;
        }
        </style>
        """
    else:
        return """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        .stApp {
            font-family: 'Inter', sans-serif !important;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%) !important;
        }
        
        .main-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 25%, #f093fb 50%, #f5576c 75%, #4facfe 100%);
            color: white;
            padding: 3rem 2rem;
            border-radius: 20px;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 20px 40px rgba(102,126,234,0.3);
            position: relative;
            overflow: hidden;
        }
        
        .main-header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.2) 50%, transparent 70%);
            animation: shimmer 3s infinite;
        }
        
        .main-header h1 {
            font-size: 3rem !important;
            font-weight: 700 !important;
            margin-bottom: 0.5rem !important;
            text-shadow: 2px 2px 8px rgba(0,0,0,0.2);
            z-index: 2;
            position: relative;
        }
        
        .main-header p {
            font-size: 1.2rem !important;
            font-weight: 300 !important;
            opacity: 0.95;
            z-index: 2;
            position: relative;
        }
        
        @keyframes shimmer {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }
        
        .nav-button {
            background: linear-gradient(145deg, #ffffff, #f7fafc) !important;
            color: #2d3748 !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 12px !important;
            padding: 0.8rem 1.5rem !important;
            font-weight: 600 !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
            margin: 0.2rem 0 !important;
        }
        
        .nav-button:hover {
            background: linear-gradient(145deg, #667eea, #764ba2) !important;
            color: white !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 25px rgba(102,126,234,0.3) !important;
        }
        
        .nav-button.active {
            background: linear-gradient(145deg, #667eea, #764ba2) !important;
            color: white !important;
            box-shadow: 0 0 20px rgba(102,126,234,0.4) !important;
        }
        
        .model-info {
            background: linear-gradient(145deg, #ffffff, #f7fafc);
            padding: 1.5rem;
            border-radius: 15px;
            margin: 1rem 0;
            border-left: 4px solid #667eea;
            box-shadow: 0 8px 20px rgba(0,0,0,0.1);
        }
        
        .success-box {
            background: linear-gradient(145deg, #f0fff4, #c6f6d5);
            border: 1px solid #48bb78;
            color: #22543d;
            padding: 2rem;
            border-radius: 15px;
            margin: 1rem 0;
            box-shadow: 0 8px 20px rgba(72,187,120,0.2);
        }
        
        .error-box {
            background: linear-gradient(145deg, #fff5f5, #fed7d7);
            border: 1px solid #f56565;
            color: #c53030;
            padding: 2rem;
            border-radius: 15px;
            margin: 1rem 0;
            box-shadow: 0 8px 20px rgba(245,101,101,0.2);
        }
        
        .scene-card {
            border: 1px solid #e2e8f0;
            border-radius: 20px;
            padding: 2rem;
            margin: 1.5rem 0;
            background: linear-gradient(145deg, #ffffff, #f7fafc);
            box-shadow: 0 12px 30px rgba(0,0,0,0.1);
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .scene-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.15);
            border-color: #667eea;
        }
        
        .metric-card {
            background: linear-gradient(145deg, #ffffff, #f7fafc);
            padding: 1.5rem;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 8px 20px rgba(0,0,0,0.1);
            border: 1px solid #e2e8f0;
        }
        
        .custom-button {
            background: linear-gradient(145deg, #667eea, #764ba2) !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 0.8rem 2rem !important;
            font-weight: 600 !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 6px 15px rgba(102,126,234,0.3) !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
        }
        
        .custom-button:hover {
            transform: translateY(-3px) !important;
            box-shadow: 0 10px 25px rgba(102,126,234,0.5) !important;
            background: linear-gradient(145deg, #764ba2, #667eea) !important;
        }
        
        .custom-button:active {
            transform: translateY(-1px) !important;
        }
        
        .primary-button {
            background: linear-gradient(145deg, #f093fb, #f5576c) !important;
            box-shadow: 0 6px 15px rgba(245,87,108,0.3) !important;
        }
        
        .primary-button:hover {
            box-shadow: 0 10px 25px rgba(245,87,108,0.5) !important;
        }
        
        .loading-spinner {
            display: inline-block;
            width: 24px;
            height: 24px;
            border: 3px solid rgba(102,126,234,.2);
            border-radius: 50%;
            border-top-color: #667eea;
            animation: loading-spin 1s ease-in-out infinite;
            margin-right: 12px;
        }
        
        @keyframes loading-spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .sidebar .nav-button {
            width: 100% !important;
            margin-bottom: 0.5rem !important;
            text-align: center !important;
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
        response = requests.post(f"{API_BASE_URL}/generate-previews", json=payload, timeout=120)
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

def start_new_project():
    """Reset session state for a new project"""
    st.session_state.current_project = None
    st.session_state.current_session = None
    st.session_state.project_created = False
    st.session_state.project_creation_result = None
    navigate_to("Create Story", delay=0.3)

# Main Header
st.markdown("""
<div class="main-header">
    <h1>🎬 Story to Image Generator</h1>
    <p>Transform your stories into stunning AI-generated images using cutting-edge AI technology</p>
</div>
""", unsafe_allow_html=True)

# Enhanced Sidebar
with st.sidebar:
    # Theme toggle button with enhanced styling
    theme_icon = "🌙" if not st.session_state.dark_theme else "☀️"
    theme_text = "Dark Mode" if not st.session_state.dark_theme else "Light Mode"
    
    if st.button(f"{theme_icon} Toggle {theme_text}", key="theme_toggle", help="Switch between light and dark themes"):
        st.session_state.dark_theme = not st.session_state.dark_theme
        st.rerun()
    
    st.markdown("---")
    
    # Backend health check with enhanced styling
    health = check_backend_health()
    if health["healthy"]:
        st.success("🟢 Backend Online")
        if "data" in health:
            data = health["data"]
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Sessions", data.get('active_sessions', 0))
            with col2:
                st.metric("Projects", data.get('total_projects', 0))
    else:
        st.error(f"🔴 Backend Offline")
        st.error(f"Error: {health['error']}")
        st.warning("Please start the backend server first!")
        st.stop()
    
    st.markdown("---")
    st.markdown("### 🧭 Navigation")
    
    # Enhanced Navigation with custom styling
    pages = [
        ("🎭 Create Story", "Create Story"),
        ("🎨 Generate Images", "Generate Images"), 
        ("📊 Monitor Progress", "Monitor Progress"),
        ("📁 My Projects", "My Projects")
    ]
    
    current_page = st.session_state.current_page
    
    for page_display, page_key in pages:
        is_active = (page_key == current_page)
        button_class = "nav-button active" if is_active else "nav-button"
        
        # Create custom styled buttons
        button_html = f"""
        <div style="margin-bottom: 0.5rem;">
            <button class="{button_class}" onclick="window.location.reload()" 
                    style="width: 100%; text-align: left; font-size: 0.9rem;">
                {page_display}
            </button>
        </div>
        """
        
        if st.button(page_display, key=f"nav_{page_key}", use_container_width=True, 
                    type="primary" if is_active else "secondary"):
            if page_key != current_page:
                navigate_to(page_key, delay=0.3)
    
    # Back button with enhanced styling
    if len(st.session_state.navigation_history) > 1:
        st.markdown("---")
        if st.button("⬅️ Go Back", use_container_width=True, help="Return to previous page"):
            go_back()
    
    # Current project info with enhanced styling
    if st.session_state.current_project:
        st.markdown("---")
        st.markdown("### 📋 Current Project")
        project = st.session_state.current_project
        
        st.info(f"""
        **ID:** {project['project_id'][:20]}...  
        **Words:** {project['analysis']['word_count']}  
        **Scenes:** {project['analysis'].get('recommended_scenes', 'N/A')}
        """)
        
        if st.button("🗑️ Clear Project", use_container_width=True, help="Clear current project selection"):
            st.session_state.current_project = None
            st.rerun()
    
    # Current session info with enhanced styling
    if st.session_state.current_session:
        st.markdown("### ⚡ Active Session")
        st.info(f"**ID:** {st.session_state.current_session[:20]}...")
        
        if st.button("🛑 End Session", use_container_width=True, help="End current generation session"):
            st.session_state.current_session = None
            st.rerun()
    
    # Quick actions
    st.markdown("---")
    st.markdown("### ⚡ Quick Actions")
    if st.button("🆕 New Project", use_container_width=True, help="Start a completely new project"):
        start_new_project()

# Page: Create Story
def create_story_page():
    st.header("🎭 Create New Story Project")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.form("script_form", clear_on_submit=False):
            title = st.text_input(
                "📝 Project Title*", 
                placeholder="Enter a descriptive title for your story",
                help="Give your project a memorable name"
            )
            
            script = st.text_area(
                "📖 Story Script*", 
                height=300,
                placeholder="Enter your story or script here...\n\nTip: The more detailed and descriptive your story, the better the AI-generated images will be!\n\nExample:\n'In a mystical forest bathed in golden sunlight, a young wizard with flowing silver robes discovers an ancient glowing crystal hidden beneath twisted oak roots. The crystal pulses with ethereal blue light, casting dancing shadows on the moss-covered ground...'",
                help="Paste or write your story content. Longer, more descriptive scripts generate better scenes."
            )
            
            # Character counter
            if script:
                word_count = len(script.split())
                char_count = len(script)
                st.caption(f"📊 {word_count} words | {char_count} characters")
                
                # Provide feedback on script length
                if word_count < 50:
                    st.warning("⚠️ Script is quite short. Consider adding more details for better results.")
                elif word_count < 100:
                    st.info("💡 Good length! Consider adding more visual descriptions.")
                elif word_count < 500:
                    st.success("✅ Excellent length for detailed scene generation!")
                else:
                    st.success("🎯 Great! Long stories will generate rich, detailed scenes.")
            
            col_form1, col_form2, col_form3 = st.columns(3)
            with col_form1:
                submitted = st.form_submit_button("🔍 Analyze & Create Project", use_container_width=True, type="primary")
            
            with col_form2:
                clear_form = st.form_submit_button("🗑️ Clear Form", use_container_width=True)
            
            with col_form3:
                if st.form_submit_button("📁 Load Example", use_container_width=True, help="Load a sample story"):
                    example_story = """In the heart of an enchanted forest, where ancient oak trees stretch their gnarled branches toward a canopy of shimmering stars, lives Luna, a young sorceress with silver hair that glows like moonlight. Her emerald eyes hold the wisdom of centuries, though she appears no older than twenty.

One fateful evening, as purple twilight painted the sky, Luna discovered a hidden grove where crystalline flowers bloomed with an otherworldly light. Each petal sang with harmonious chimes when touched by the gentle breeze. At the center of this magical garden stood an ornate pedestal holding a mysterious orb that pulsed with swirling galaxies inside.

As Luna approached, the orb began to levitate, casting rainbow reflections across her flowing indigo robes. The ground beneath her feet sparkled with stardust, and the air filled with floating luminous particles. She reached out with trembling hands, knowing this moment would change her destiny forever.

When her fingertips touched the orb's surface, visions of distant realms flashed before her eyes - floating cities among the clouds, underwater kingdoms with coral spires, and mountain peaks crowned with phoenix nests. The magic within her awakened, and golden light began to emanate from her entire being.

With newfound power coursing through her veins, Luna realized she had become the guardian of the cosmic balance, destined to protect all realms from the encroaching darkness that threatened to consume the multiverse."""
                    
                    # This will update the form fields, but since we can't directly modify form inputs,
                    # we'll store it in session state and rerun
                    st.session_state.example_story = example_story
                    st.session_state.example_title = "Luna and the Cosmic Orb"
                    st.rerun()
                
            if clear_form:
                if 'example_story' in st.session_state:
                    del st.session_state.example_story
                if 'example_title' in st.session_state:
                    del st.session_state.example_title
                st.rerun()
                
            # Handle example loading
            if 'example_story' in st.session_state and 'example_title' in st.session_state:
                st.info("📝 Example story loaded! Click 'Analyze & Create Project' to proceed.")
                script = st.session_state.example_story
                title = st.session_state.example_title
                
            if submitted:
                if not title.strip():
                    st.error("❌ Please provide a project title")
                    return
                    
                if not script.strip():
                    st.error("❌ Please provide a story script")
                    return
                
                if len(script.split()) < 10:
                    st.error("❌ Script too short. Please provide at least 10 words for meaningful analysis.")
                    return
                
                with st.spinner("🔍 Analyzing script and creating project..."):
                    result = analyze_script(script.strip(), title.strip())
                
                if result:
                    st.session_state.current_project = result
                    st.session_state.project_created = True
                    st.session_state.project_creation_result = result
                    
                    # Clear example if it was used
                    if 'example_story' in st.session_state:
                        del st.session_state.example_story
                    if 'example_title' in st.session_state:
                        del st.session_state.example_title
                    
                    st.markdown(f"""
                    <div class="success-box">
                        <h3>🎉 Project Created Successfully!</h3>
                        <p><strong>Project ID:</strong> {result['project_id']}</p>
                        <p><strong>Word Count:</strong> {result['analysis']['word_count']} words</p>
                        <p><strong>Recommended Scenes:</strong> {result['analysis']['recommended_scenes']} scenes</p>
                        <p><strong>Estimated Duration:</strong> {result['analysis']['estimated_duration_minutes']:.1f} minutes</p>
                        <p><strong>Complexity:</strong> {result['analysis']['complexity_score']}</p>
                    </div>
                    """, unsafe_allow_html=True)

                    time.sleep(2)
                    navigate_to("Generate Images", delay=0.5)
    
    with col2:
        st.markdown("### 💡 Tips for Better Results")
        
        with st.expander("✍️ Writing Tips", expanded=True):
            st.info("""
            **🎨 Visual Descriptions:**
            • Use rich, descriptive language
            • Include colors, lighting, and atmosphere
            • Describe characters' appearance and clothing
            • Set vivid scenes and environments
            
            **📝 Structure Tips:**
            • Break your story into clear scenes
            • Include dialogue and action
            • Mention specific details and props
            • Describe emotions and mood
            """)
        
        with st.expander("📏 Length Guidelines"):
            st.info("""
            **Script Length Guide:**
            • **Short (50-100 words):** 2-4 scenes
            • **Medium (100-300 words):** 4-8 scenes  
            • **Long (300-500 words):** 8-12 scenes
            • **Epic (500+ words):** 12+ scenes
            
            **Quality over Quantity:**
            Detailed descriptions create better images than long but vague text.
            """)
        
        with st.expander("🎭 Style Examples"):
            st.info("""
            **🎬 Cinematic:** Movie-like dramatic scenes
            • "The camera pans across..."
            • "Close-up of character's eyes..."
            
            **🎨 Cartoon:** Animated, colorful style
            • "Vibrant colors pop against..."
            • "Exaggerated expressions..."
            
            **📸 Realistic:** Photo-realistic images
            • "Natural lighting reveals..."
            • "Detailed textures show..."
            
            **🖼️ Artistic:** Creative interpretation
            • "Painterly brushstrokes..."
            • "Abstract representation of..."
            """)
        
        # Show available models info
        if st.session_state.available_models:
            models = st.session_state.available_models
            
            with st.expander("🤖 Available AI Models"):
                ai_models = models.get("ai_models", {}).get("openrouter", [])
                image_models = models.get("image_models", {})
                runware_count = len(image_models.get("runware", []))
                together_count = len(image_models.get("together", []))
                openrouter_image_count = len(image_models.get("openrouter_imgae", []))
                
                st.success(f"**🧠 AI Models:** {len(ai_models)} available")
                st.success(f"**🎨 Runware Models:** {runware_count} available")
                st.success(f"**🔧 Together AI Models:** {together_count} available")
                st.success(f"**🌐 OpenRouter Image Models:** {openrouter_image_count} available")

# Page: Generate Images
def generate_images_page():
    st.header("🎨 Generate Images from Story")
    
    # Show project creation success message if just created
    if st.session_state.project_creation_result:
        result = st.session_state.project_creation_result
        st.markdown(f"""
        <div class="success-box">
            <h3>🚀 Project Ready for Image Generation!</h3>
            <p><strong>Project ID:</strong> {result['project_id']}</p>
            <p><strong>Word Count:</strong> {result['analysis']['word_count']} words</p>
            <p><strong>Recommended Scenes:</strong> {result['analysis']['recommended_scenes']} scenes</p>
            <p><strong>Estimated Duration:</strong> {result['analysis']['estimated_duration_minutes']:.1f} minutes</p>
            <p><strong>Complexity:</strong> {result['analysis']['complexity_score']}</p>
        </div>
        """, unsafe_allow_html=True)
        # Clear after showing
        st.session_state.project_creation_result = None
    
    # Project selection
    if not st.session_state.current_project:
        st.warning("⚠️ No project selected. Please create a project first or select from existing projects.")
        
        col_action1, col_action2 = st.columns(2)
        with col_action1:
            if st.button("🆕 Create New Project", use_container_width=True, type="primary"):
                navigate_to("Create Story")
        with col_action2:
            if st.button("📁 View My Projects", use_container_width=True):
                navigate_to("My Projects")
        
        projects = load_projects()
        if projects and "projects" in projects and projects["projects"]:
            st.markdown("### 📂 Select from Recent Projects")
            
            for i, project in enumerate(projects["projects"][:5]):
                with st.expander(f"📄 {project['project_id']}", expanded=(i == 0)):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.write(f"**Words:** {project['analysis'].get('word_count', 0)}")
                        st.write(f"**Recommended Scenes:** {project['analysis'].get('recommended_scenes', 0)}")
                        st.write(f"**Complexity:** {project['analysis'].get('complexity_score', 'N/A')}")
                    
                    with col2:
                        if st.button("✅ Select", key=f"select_{project['project_id']}", use_container_width=True):
                            st.session_state.current_project = project
                            st.success(f"Selected: {project['project_id'][:20]}...")
                            time.sleep(1)
                            st.rerun()
                    
                    with col3:
                        if st.button("👁️ View", key=f"view_{project['project_id']}", use_container_width=True):
                            navigate_to("My Projects")
        
        # Manual project ID entry
        with st.expander("🔧 Advanced: Enter Project ID Manually"):
            manual_project_id = st.text_input(
                "Project ID:", 
                placeholder="story_20241201_123456",
                help="Enter the exact project ID if you know it"
            )
            
            if manual_project_id and st.button("📥 Load Project", use_container_width=True):
                try:
                    response = requests.get(f"{API_BASE_URL}/projects/{manual_project_id}", timeout=30)
                    if response.status_code == 200:
                        project_data = response.json()
                        st.session_state.current_project = {
                            "project_id": manual_project_id,
                            "analysis": {"word_count": len(project_data["script"].split())}
                        }
                        st.success(f"✅ Loaded project: {manual_project_id}")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ Project not found: {manual_project_id}")
                except Exception as e:
                    st.error(f"❌ Error loading project: {str(e)}")
        
        return
    
    # Show current project
    project = st.session_state.current_project
    st.success(f"📋 **Current Project:** {project['project_id']} ({project['analysis']['word_count']} words)")
    
    # Model selection
    models = st.session_state.available_models
    if not models:
        st.error("❌ Failed to load available models. Please check backend connection.")
        return
    
    st.markdown("### ⚙️ Generation Settings")
    
    # Enhanced settings layout with 4 columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("#### 🧠 AI Scene Analysis")
        
        ai_models = models.get("ai_models", {}).get("openrouter", [])
        if ai_models:
            ai_model = st.selectbox("AI Model:", ai_models, help="Choose AI model for scene analysis")
            
            # Enhanced model descriptions
            model_descriptions = {
                "gpt-4o-mini": "💡 Fast and efficient GPT-4 Omni Mini",
                "gpt-4.1-mini": "⚡ Advanced GPT-4.1 Mini model",
                "openai/gpt-4o-mini": "🚀 OpenAI GPT-4 Omni optimized",
                "meta-llama/llama-3.1-8b-instruct:free": "🦙 Creative Llama 3.1 (Free)",
                "microsoft/phi-3-mini-128k-instruct:free": "🔧 Microsoft Phi-3 (Free)"
            }
            
            if ai_model in model_descriptions:
                st.info(model_descriptions[ai_model])
            else:
                st.info("🤖 Selected AI model for scene generation")
        else:
            st.warning("⚠️ No AI models available, using fallback")
            ai_model = "fallback"
    
    with col2:
        st.markdown("#### 🎨 Image Generation")
        
        # Include all three providers including OpenRouter Image
        image_provider = st.selectbox("Image Provider:", ["runware", "together", "openrouter_imgae"])
        
        if image_provider == "runware":
            runware_models = models.get("image_models", {}).get("runware", [])
            if runware_models:
                image_model = st.selectbox("Runware Model:", runware_models)
                st.info("🚀 High-quality, fast generation")
            else:
                st.error("❌ No Runware models available")
                return
        elif image_provider == "together":
            together_models = models.get("image_models", {}).get("together", [])
            if together_models:
                image_model = st.selectbox("Together Model:", together_models)
                st.info("🔧 Diverse model options with FLUX")
            else:
                st.error("❌ No Together AI models available")
                return
        else:  # openrouter_imgae
            openrouter_image_models = models.get("image_models", {}).get("openrouter_imgae", [])
            if openrouter_image_models:
                image_model = st.selectbox("OpenRouter Image Model:", openrouter_image_models)
                st.info("🌐 Advanced Gemini vision models")
            else:
                st.error("❌ No OpenRouter image models available")
                return
    
    with col3:
        st.markdown("#### 🎭 Visual Style")
        
        media_type = st.selectbox("Visual Style:", [
            "cinematic", "cartoon", "realistic", "artistic"
        ], help="Choose the visual style for your images")
        
        # Enhanced style preview with emojis
        style_descriptions = {
            "cinematic": "🎬 Movie-like with dramatic lighting",
            "cartoon": "🎨 Vibrant animated style with bold colors", 
            "realistic": "📸 Photorealistic with natural lighting",
            "artistic": "🖼️ Creative artistic interpretation"
        }
        
        st.info(style_descriptions.get(media_type, 'Custom style selected'))
    
    with col4:
        st.markdown("#### 📊 Scene Count")
        
        # Enhanced scene input with no maximum limit
        recommended_scenes = project['analysis'].get('recommended_scenes', 4)
        
        num_scenes = st.number_input(
            "Number of scenes:", 
            min_value=1, 
            max_value=50,  # Increased from 10 to 50
            value=recommended_scenes,
            help=f"Recommended: {recommended_scenes} scenes based on your story length. You can generate up to 50 scenes!"
        )
        
        # Scene count feedback
        if num_scenes <= recommended_scenes:
            st.success(f"✅ Optimal count")
        elif num_scenes <= recommended_scenes + 3:
            st.info(f"💡 Good for detailed breakdown")
        else:
            st.warning(f"⚠️ Many scenes - longer generation time")
    
    # Enhanced style preview section
    st.markdown("---")
    st.markdown("### 🎨 Selected Configuration Preview")
    
    config_col1, config_col2, config_col3 = st.columns(3)
    
    with config_col1:
        st.markdown(f"""
        <div class="metric-card">
            <h4>🧠 AI Analysis</h4>
            <p><strong>{ai_model}</strong></p>
            <small>Scene generation & prompts</small>
        </div>
        """, unsafe_allow_html=True)
    
    with config_col2:
        st.markdown(f"""
        <div class="metric-card">
            <h4>🎨 Image Provider</h4>
            <p><strong>{image_provider.title()}</strong></p>
            <small>{image_model}</small>
        </div>
        """, unsafe_allow_html=True)
    
    with config_col3:
        st.markdown(f"""
        <div class="metric-card">
            <h4>🎭 Style & Scenes</h4>
            <p><strong>{media_type.title()}</strong></p>
            <small>{num_scenes} scenes to generate</small>
        </div>
        """, unsafe_allow_html=True)
    
    # Enhanced navigation and action buttons
    st.markdown("---")
    col_nav1, col_nav2, col_nav3, col_nav4 = st.columns(4)
    
    with col_nav1:
        if st.button("⬅️ Back to Create Story", use_container_width=True):
            navigate_to("Create Story")
    
    with col_nav2:
        if st.button("🗑️ Clear Project", use_container_width=True):
            st.session_state.current_project = None
            st.rerun()
    
    with col_nav3:
        if st.button("📁 My Projects", use_container_width=True):
            navigate_to("My Projects")
    
    with col_nav4:
        generate_clicked = st.button("🚀 Generate Scene Previews", use_container_width=True, type="primary")
    
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
        
        with st.spinner("🚀 Starting generation process..."):
            result = start_generation(payload)
        
        if result:
            st.session_state.current_session = result["session_id"]
            
            st.markdown(f"""
            <div class="success-box">
                <h3>🎉 Generation Started Successfully!</h3>
                <p><strong>Session ID:</strong> {result['session_id']}</p>
                <p><strong>Total Scenes:</strong> {result['total_scenes']}</p>
                <p><strong>Status:</strong> {result['status'].title()}</p>
                <p><strong>Provider:</strong> {image_provider.title()}</p>
                <p><strong>Style:</strong> {media_type.title()}</p>
            </div>
            """, unsafe_allow_html=True)
            
            time.sleep(2)
            navigate_to("Monitor Progress", delay=0.5)

# Page: Monitor Progress (Enhanced)
def monitor_progress_page():
    st.header("📊 Monitor Generation Progress")
    
    # Session selection
    if st.session_state.current_session:
        session_id = st.text_input(
            "🔍 Session ID:", 
            value=st.session_state.current_session,
            help="Current active session"
        )
    else:
        session_id = st.text_input(
            "🔍 Session ID:", 
            placeholder="session_abcd1234",
            help="Enter session ID to monitor"
        )
    
    if not session_id:
        st.info("💡 Enter a session ID to monitor progress")
        
        col_back1, col_back2 = st.columns(2)
        with col_back1:
            if st.button("⬅️ Back to Generate Images", use_container_width=True):
                navigate_to("Generate Images")
        with col_back2:
            if st.button("📁 My Projects", use_container_width=True):
                navigate_to("My Projects")
        return
    
    # Enhanced control buttons
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        auto_refresh = st.checkbox("🔄 Auto-refresh", value=True, help="Automatically update every 1.5 seconds")
    
    with col2:
        manual_refresh = st.button("📊 Check Status", help="Manually check current status")
    
    with col3:
        if st.button("⬅️ Back to Generate"):
            navigate_to("Generate Images")
    
    with col4:
        if st.button("🗑️ Clear Session"):
            st.session_state.current_session = None
            st.rerun()
    
    with col5:
        if st.button("🆕 New Project"):
            start_new_project()
    
    if manual_refresh or auto_refresh:
        status = get_generation_status(session_id)
        
        if not status:
            st.error("❌ Session not found or expired")
            col_error1, col_error2 = st.columns(2)
            with col_error1:
                if st.button("🔄 Try Different Session", use_container_width=True):
                    st.session_state.current_session = None
                    st.rerun()
            with col_error2:
                if st.button("🆕 Start New Project", use_container_width=True):
                    start_new_project()
            return
        
        # Enhanced progress display
        progress = status["completed_scenes"] / max(status["total_scenes"], 1)
        st.progress(progress, text=f"Progress: {status['completed_scenes']}/{status['total_scenes']} scenes ({progress*100:.1f}%)")
        
        # Enhanced status metrics with better styling
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            status_icons = {"generating": "🟡", "previewing": "🔵", "completed": "🟢", "failed": "🔴"}
            status_colors = {"generating": "#FFA500", "previewing": "#4169E1", "completed": "#32CD32", "failed": "#FF4500"}
            current_status = status['status']
            
            st.markdown(f"""
            <div class="metric-card">
                <h3>{status_icons.get(current_status, '⚪')} Status</h3>
                <p style="color: {status_colors.get(current_status, '#666')}"><strong>{current_status.title()}</strong></p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            completion_percent = int(progress * 100)
            st.markdown(f"""
            <div class="metric-card">
                <h3>📊 Progress</h3>
                <p><strong>{status['completed_scenes']}/{status['total_scenes']}</strong></p>
                <small>{completion_percent}% complete</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <h3>🎬 Total Scenes</h3>
                <p><strong>{status['total_scenes']}</strong></p>
                <small>Images to generate</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            error_count = len(status.get("errors", []))
            error_color = "#FF4500" if error_count > 0 else "#32CD32"
            error_icon = "🔴" if error_count > 0 else "🟢"
            
            st.markdown(f"""
            <div class="metric-card">
                <h3>{error_icon} Errors</h3>
                <p style="color: {error_color}"><strong>{error_count}</strong></p>
                <small>Generation issues</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col5:
            # Estimate time remaining
            if status["status"] == "generating" and status["completed_scenes"] > 0:
                avg_time_per_scene = 30  # Estimated seconds per scene
                remaining_scenes = status["total_scenes"] - status["completed_scenes"]
                estimated_remaining = remaining_scenes * avg_time_per_scene
                
                if estimated_remaining < 60:
                    time_text = f"{estimated_remaining:.0f}s"
                else:
                    time_text = f"{estimated_remaining/60:.1f}m"
                
                st.markdown(f"""
                <div class="metric-card">
                    <h3>⏱️ Est. Time</h3>
                    <p><strong>{time_text}</strong></p>
                    <small>Remaining</small>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="metric-card">
                    <h3>⏱️ Session</h3>
                    <p><strong>Active</strong></p>
                    <small>Generation session</small>
                </div>
                """, unsafe_allow_html=True)
        
        # Enhanced error display
        if status.get("errors"):
            with st.expander(f"⚠️ View Errors ({len(status['errors'])})", expanded=len(status['errors']) > 0):
                for i, error in enumerate(status["errors"], 1):
                    st.error(f"**Error {i}:** {error}")
        
        # Enhanced generation status messages
        if status["status"] == "generating":
            st.markdown("""
            <div class="success-box" style="background: linear-gradient(145deg, rgba(255,193,7,0.2), rgba(255,193,7,0.1)); border-color: #FFC107; color: #FF8F00;">
                <h3>🚀 Generation In Progress</h3>
                <p>AI is creating your scene images. This may take several minutes depending on the number of scenes and model complexity.</p>
                <p><strong>💡 Tip:</strong> You can safely close this tab and return later - your session will continue running!</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Enhanced previews display
        if status["previews"]:
            st.markdown("---")
            st.subheader("🖼️ Generated Previews")
            
            # Approval section for completed generation
            if status["status"] in ["previewing", "completed"]:
                
                # Sort previews by scene number for consistent display
                sorted_previews = sorted(status["previews"], key=lambda x: x["scene_number"])
                
                # Display previews in an enhanced grid
                cols_per_row = 2  # Reduced for better mobile experience
                approvals = {}
                regenerate_requests = {}
                
                for i, preview in enumerate(sorted_previews):
                    if i % cols_per_row == 0:
                        cols = st.columns(cols_per_row)
                    
                    with cols[i % cols_per_row]:
                        st.markdown(f"""
                        <div class="scene-card">
                            <h4>🎬 Scene {preview['scene_number']}: {preview['scene_title']}</h4>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if preview["preview_url"]:
                            st.image(preview["preview_url"], use_container_width=True)
                            
                            # Enhanced approval section
                            col_approve, col_regen = st.columns(2)
                            
                            with col_approve:
                                # Approval checkbox
                                approvals[str(preview["scene_number"])] = st.checkbox(
                                    f"✅ Save Scene {preview['scene_number']}", 
                                    value=True,
                                    key=f"approve_{preview['scene_number']}_{session_id}",
                                    help="Check to include this scene in final output"
                                )
                            
                            with col_regen:
                                # Regenerate button
                                if st.button(
                                    "🔄 Regenerate", 
                                    key=f"regen_{preview['scene_number']}_{session_id}",
                                    help="Generate a new version of this scene",
                                    use_container_width=True
                                ):
                                    regenerate_requests[preview["scene_number"]] = {
                                        "provider": preview["provider_used"],
                                        "model": preview["model_used"]
                                    }
                            
                            # Enhanced scene details
                            with st.expander(f"📋 Scene {preview['scene_number']} Details"):
                                st.text_area(
                                    "Image Prompt:", 
                                    preview['prompt'], 
                                    height=100, 
                                    disabled=True,
                                    key=f"prompt_{preview['scene_number']}_{session_id}"
                                )
                                
                                detail_col1, detail_col2 = st.columns(2)
                                with detail_col1:
                                    st.caption(f"⏱️ Generation time: {preview['generation_time']:.1f}s")
                                    st.caption(f"🏢 Provider: {preview['provider_used']}")
                                with detail_col2:
                                    st.caption(f"🤖 Model: {preview['model_used']}")
                                    if preview.get('approved'):
                                        st.caption("✅ Approved for saving")
                                
                                if preview.get('error'):
                                    st.error(f"❌ Error: {preview['error']}")
                        else:
                            # Enhanced failed scene display
                            st.markdown(f"""
                            <div class="error-box">
                                <h4>❌ Generation Failed</h4>
                                <p><strong>Scene {preview['scene_number']}:</strong> {preview['scene_title']}</p>
                                <p><strong>Error:</strong> {preview.get('error', 'Unknown error occurred')}</p>
                                <p><strong>Provider:</strong> {preview['provider_used']} | <strong>Model:</strong> {preview['model_used']}</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Enhanced regeneration options for failed scenes
                            col_regen1, col_regen2, col_regen3 = st.columns(3)
                            
                            with col_regen1:
                                if st.button(
                                    f"🔄 Retry Same", 
                                    key=f"retry_{preview['scene_number']}_{session_id}",
                                    help="Try generating this scene again with same provider",
                                    use_container_width=True
                                ):
                                    regenerate_requests[preview["scene_number"]] = {
                                        "provider": preview["provider_used"],
                                        "model": preview["model_used"]
                                    }
                            
                            with col_regen2:
                                # Try alternative provider
                                current_provider = preview["provider_used"]
                                if current_provider == "runware":
                                    alt_provider = "together"
                                elif current_provider == "together":
                                    alt_provider = "openrouter_imgae"
                                else:
                                    alt_provider = "runware"
                                
                                if st.button(
                                    f"🔧 Try {alt_provider.title()}", 
                                    key=f"alt1_{preview['scene_number']}_{session_id}",
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
                            
                            with col_regen3:
                                # Try third provider option
                                current_provider = preview["provider_used"]
                                providers = ["runware", "together", "openrouter_imgae"]
                                available_providers = [p for p in providers if p != current_provider]
                                
                                if len(available_providers) > 1:
                                    third_provider = available_providers[1]
                                    if st.button(
                                        f"🌐 Try {third_provider.title()}", 
                                        key=f"alt2_{preview['scene_number']}_{session_id}",
                                        help=f"Try generating with {third_provider} instead",
                                        use_container_width=True
                                    ):
                                        models = st.session_state.available_models
                                        alt_models = models.get("image_models", {}).get(third_provider, [])
                                        if alt_models:
                                            regenerate_requests[preview["scene_number"]] = {
                                                "provider": third_provider,
                                                "model": alt_models[0]
                                            }
                            
                            approvals[str(preview["scene_number"])] = False
                
                # Handle regeneration requests with enhanced feedback
                for scene_num, regen_info in regenerate_requests.items():
                    with st.spinner(f"🔄 Regenerating scene {scene_num} with {regen_info['provider']}..."):
                        regen_result = regenerate_scene(
                            session_id, 
                            scene_num,
                            regen_info["provider"],
                            regen_info["model"]
                        )
                    
                    if regen_result and regen_result.get("status") == "success":
                        st.success(f"✅ Scene {scene_num} regenerated successfully with {regen_info['provider']}!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to regenerate scene {scene_num} with {regen_info['provider']}")
                
                # Enhanced approval form
                st.markdown("---")
                st.markdown("### 💾 Save Selected Scenes")
                
                selected_count = sum(1 for approved in approvals.values() if approved)
                total_scenes = len(status['previews'])
                successful_scenes = len([p for p in status['previews'] if p['preview_url']])
                failed_scenes = total_scenes - successful_scenes
                
                # Enhanced statistics display
                stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
                
                with stats_col1:
                    st.metric("Selected", selected_count, help="Scenes selected for saving")
                
                with stats_col2:
                    st.metric("Successful", successful_scenes, help="Successfully generated scenes")
                
                with stats_col3:
                    st.metric("Failed", failed_scenes, help="Failed generation attempts")
                
                with stats_col4:
                    st.metric("Total", total_scenes, help="Total scenes in project")
                
                if selected_count == 0:
                    st.warning("⚠️ No scenes selected for saving. Please select at least one scene.")
                else:
                    st.info(f"📊 **{selected_count}** out of **{successful_scenes}** successful scenes selected for saving")
                
                # Enhanced save buttons
                col_save1, col_save2, col_save3, col_save4 = st.columns(4)
                
                with col_save1:
                    if st.button("💾 Save Selected Scenes", disabled=selected_count == 0, use_container_width=True, type="primary"):
                        with st.spinner("💾 Saving approved scenes..."):
                            result = approve_previews(session_id, approvals)
                        
                        if result:
                            st.markdown(f"""
                            <div class="success-box">
                                <h3>🎉 Scenes Saved Successfully!</h3>
                                <p><strong>💾 Saved Images:</strong> {result['saved_images']}</p>
                                <p><strong>📊 Total Scenes:</strong> {result['total_scenes']}</p>
                                <p><strong>📁 Location:</strong> Project images folder</p>
                                <p>✅ Your images are now saved and ready to use!</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            time.sleep(2)
                            # Navigate to projects page after saving
                            navigate_to("My Projects", delay=0.5)
                
                with col_save2:
                    if st.button("✅ Select All Successful", use_container_width=True):
                        # Select all successful scenes
                        for preview in status['previews']:
                            if preview['preview_url']:
                                approvals[str(preview['scene_number'])] = True
                        st.rerun()
                
                with col_save3:
                    if st.button("❌ Deselect All", use_container_width=True):
                        # Deselect all scenes
                        for preview in status['previews']:
                            approvals[str(preview['scene_number'])] = False
                        st.rerun()
                
                with col_save4:
                    if st.button("🆕 Start New Project", use_container_width=True):
                        start_new_project()
        
        # Auto-refresh logic with enhanced user feedback
        if auto_refresh and status["status"] == "generating":
            # Show countdown for next refresh
            with st.empty():
                for remaining in range(int(POLLING_INTERVAL), 0, -1):
                    st.caption(f"🔄 Auto-refreshing in {remaining} seconds...")
                    time.sleep(1)
            st.rerun()

# Page: My Projects (Enhanced)
def my_projects_page():
    st.header("📁 My Projects")
    
    projects = load_projects()
    
    if not projects or not projects.get("projects"):
        st.info("💡 No projects found. Create your first project to get started!")
        
        col_empty1, col_empty2 = st.columns(2)
        with col_empty1:
            if st.button("🆕 Create New Project", use_container_width=True, type="primary"):
                navigate_to("Create Story", delay=0.3)
        with col_empty2:
            if st.button("🔄 Refresh Projects", use_container_width=True):
                st.cache_data.clear()
                st.rerun()
        return
    
    project_list = projects["projects"]
    st.success(f"📊 Found **{len(project_list)}** projects")
    
    # Enhanced search and filter section
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_term = st.text_input("🔍 Search projects:", placeholder="Enter project ID or keyword")
    
    with col2:
        sort_options = ["Newest First", "Oldest First", "Most Words", "Least Words", "Most Complex", "Simplest"]
        sort_by = st.selectbox("📊 Sort by:", sort_options)
    
    with col3:
        if st.button("🔄 Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    # Filter and sort projects
    filtered_projects = project_list
    
    if search_term:
        filtered_projects = [
            p for p in project_list 
            if search_term.lower() in p['project_id'].lower()
        ]
    
    # Enhanced sort logic
    if sort_by == "Newest First":
        filtered_projects = sorted(filtered_projects, key=lambda x: x['created_at'], reverse=True)
    elif sort_by == "Oldest First":
        filtered_projects = sorted(filtered_projects, key=lambda x: x['created_at'])
    elif sort_by == "Most Words":
        filtered_projects = sorted(filtered_projects, key=lambda x: x['analysis'].get('word_count', 0), reverse=True)
    elif sort_by == "Least Words":
        filtered_projects = sorted(filtered_projects, key=lambda x: x['analysis'].get('word_count', 0))
    elif sort_by == "Most Complex":
        complexity_order = {"Complex": 3, "Moderate": 2, "Simple": 1}
        filtered_projects = sorted(filtered_projects, 
                                 key=lambda x: complexity_order.get(x['analysis'].get('complexity_score', 'Simple'), 1), 
                                 reverse=True)
    elif sort_by == "Simplest":
        complexity_order = {"Complex": 3, "Moderate": 2, "Simple": 1}
        filtered_projects = sorted(filtered_projects, 
                                 key=lambda x: complexity_order.get(x['analysis'].get('complexity_score', 'Simple'), 1))
    
    st.markdown(f"📋 Showing **{len(filtered_projects)}** projects")
    
    if len(filtered_projects) == 0:
        st.warning(f"🔍 No projects found matching '{search_term}'")
        return
    
    # Enhanced project display
    for i, project in enumerate(filtered_projects):
        # Determine complexity emoji
        complexity = project['analysis'].get('complexity_score', 'Simple')
        complexity_emoji = {"Simple": "🟢", "Moderate": "🟡", "Complex": "🔴"}.get(complexity, "⚪")
        
        with st.expander(
            f"{complexity_emoji} **{project['project_id']}** - {project['analysis'].get('word_count', 0)} words | {complexity}",
            expanded=(i < 2)  # Only expand first 2 projects
        ):
            # Enhanced project layout
            main_col, action_col = st.columns([3, 1])
            
            with main_col:
                # Project metadata in organized layout
                meta_col1, meta_col2 = st.columns(2)
                
                with meta_col1:
                    created_date = project['created_at'][:19].replace('T', ' ')
                    st.markdown(f"""
                    📅 **Created:** {created_date}  
                    📊 **Word Count:** {project['analysis'].get('word_count', 'N/A')} words  
                    🎬 **Recommended Scenes:** {project['analysis'].get('recommended_scenes', 'N/A')} scenes  
                    """)
                
                with meta_col2:
                    st.markdown(f"""
                    ⏱️ **Est. Duration:** {project['analysis'].get('estimated_duration_minutes', 'N/A')} minutes  
                    🧠 **Complexity:** {complexity_emoji} {complexity}  
                    📝 **Project ID:** `{project['project_id']}`
                    """)
                
                # Enhanced project details loading
                try:
                    response = requests.get(f"{API_BASE_URL}/projects/{project['project_id']}", timeout=10)
                    if response.status_code == 200:
                        details = response.json()
                        
                        if details.get('images'):
                            image_count = len(details['images'])
                            st.success(f"🖼️ **{image_count} images generated** ✅")
                            
                            # Enhanced thumbnail gallery
                            if image_count > 0:
                                st.markdown("**🖼️ Generated Images:**")
                                
                                # Show thumbnails in a responsive grid
                                max_display = min(6, image_count)
                                img_cols = st.columns(max_display)
                                
                                for idx, img_path in enumerate(details['images'][:max_display]):
                                    with img_cols[idx]:
                                        try:
                                            img_url = f"{API_BASE_URL}{img_path}"
                                            st.image(img_url, use_container_width=True, caption=f"Scene {idx+1}")
                                        except:
                                            st.error("❌ Image load failed")
                                
                                if image_count > max_display:
                                    st.caption(f"➕ ... and {image_count - max_display} more images")
                        else:
                            st.info("📝 Project created - No images generated yet")
                            
                    else:
                        st.warning("⚠️ Could not load full project details")
                        
                except requests.exceptions.Timeout:
                    st.warning("⏱️ Project details loading timed out")
                except Exception as e:
                    st.error(f"❌ Error loading project: {str(e)}")
            
            with action_col:
                st.markdown("### 🎯 Actions")
                
                # Enhanced action buttons with better spacing and icons
                if st.button("🎨 Generate Images", key=f"gen_{project['project_id']}", use_container_width=True, type="primary"):
                    st.session_state.current_project = project
                    st.success(f"✅ Project selected: {project['project_id'][:15]}...")
                    time.sleep(1)
                    navigate_to("Generate Images", delay=0.3)
                
                if st.button("📋 Use Project", key=f"use_{project['project_id']}", use_container_width=True):
                    st.session_state.current_project = project
                    st.success(f"✅ Selected: {project['project_id'][:15]}...")
                    time.sleep(1)
                    st.rerun()
                
                if st.button("👁️ View Details", key=f"view_{project['project_id']}", use_container_width=True):
                    # Enhanced detailed view
                    try:
                        response = requests.get(f"{API_BASE_URL}/projects/{project['project_id']}", timeout=15)
                        if response.status_code == 200:
                            details = response.json()
                            
                            # Create a detailed modal-like view
                            st.markdown(f"---")
                            st.markdown(f"### 📄 Full Project Details - {project['project_id']}")
                            
                            # Script content with enhanced styling
                            with st.expander("📖 Original Script Content", expanded=False):
                                script_text = details['script']
                                word_count = len(script_text.split())
                                st.markdown(f"**Word Count:** {word_count} words")
                                st.text_area("Script:", script_text, height=300, disabled=True, key=f"script_detail_{project['project_id']}")
                            
                            # Images gallery with enhanced display
                            if details.get('images'):
                                st.markdown("### 🖼️ All Generated Images")
                                
                                images = details['images']
                                st.success(f"📊 Total images: {len(images)}")
                                
                                # Display images in a responsive grid
                                cols_per_row = 3
                                for idx in range(0, len(images), cols_per_row):
                                    img_cols = st.columns(cols_per_row)
                                    
                                    for col_idx, img_path in enumerate(images[idx:idx+cols_per_row]):
                                        with img_cols[col_idx]:
                                            try:
                                                img_url = f"{API_BASE_URL}{img_path}"
                                                st.image(img_url, use_container_width=True, caption=f"Scene {idx + col_idx + 1}")
                                                
                                                # Download link (if possible)
                                                st.markdown(f"[🔗 Direct Link]({img_url})")
                                            except Exception as e:
                                                st.error(f"❌ Could not load Scene {idx + col_idx + 1}")
                            else:
                                st.info("📝 No images generated for this project yet")
                                
                    except requests.exceptions.Timeout:
                        st.error("⏱️ Request timed out while loading project details")
                    except Exception as e:
                        st.error(f"❌ Error loading project details: {str(e)}")
                
                # Quick actions
                st.markdown("---")
                if st.button("🗑️ Archive", key=f"archive_{project['project_id']}", use_container_width=True, help="Archive this project (not implemented)"):
                    st.info("🚧 Archive functionality coming soon!")

# Main Navigation Router with enhanced transitions
current_page = st.session_state.current_page

# Add page transition indicator
with st.container():
    if current_page == "Create Story":
        create_story_page()
    elif current_page == "Generate Images":
        generate_images_page()
    elif current_page == "Monitor Progress":
        monitor_progress_page()
    elif current_page == "My Projects":
        my_projects_page()

# Enhanced Footer with additional information
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem; background: linear-gradient(145deg, #f8f9fa, #e9ecef); border-radius: 15px; margin-top: 2rem; box-shadow: 0 8px 20px rgba(0,0,0,0.1);">
    <h4>🎬 Story to Image Generator v3.0</h4>
    <p>Powered by <strong>🌐 OpenRouter</strong>, <strong>🚀 Runware</strong>, <strong>🔧 Together AI</strong> & <strong>🧠 Gemini Vision</strong></p>
    <p style="font-size: 0.9em; color: #888;">Transform your stories into stunning AI-generated images with cutting-edge technology</p>
    <p style="font-size: 0.8em; color: #aaa;">
        Features: Multi-Provider Image Generation | Advanced Scene Analysis | Flexible Scene Count | Enhanced UI/UX
    </p>
</div>
""", unsafe_allow_html=True)

# Enhanced Debug Information (only show in development)
if st.checkbox("🛠️ Debug Mode", value=False, help="Show technical information for debugging"):
    st.markdown("---")
    st.markdown("### 🔧 Debug Information")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**🧭 Navigation State:**")
        st.json({
            "current_page": st.session_state.current_page,
            "navigation_history": st.session_state.navigation_history[-3:],
            "has_current_project": st.session_state.current_project is not None,
            "has_current_session": st.session_state.current_session is not None,
            "dark_theme": st.session_state.dark_theme
        })
    
    with col2:
        st.markdown("**📋 Project State:**")
        if st.session_state.current_project:
            st.json({
                "project_id": st.session_state.current_project.get("project_id"),
                "word_count": st.session_state.current_project.get("analysis", {}).get("word_count"),
                "recommended_scenes": st.session_state.current_project.get("analysis", {}).get("recommended_scenes"),
                "complexity": st.session_state.current_project.get("analysis", {}).get("complexity_score")
            })
        else:
            st.info("No current project")
    
    with col3:
        st.markdown("**⚡ Session State:**")
        if st.session_state.current_session:
            st.text(f"Session: {st.session_state.current_session}")
            
            # Try to get session status
            try:
                status = get_generation_status(st.session_state.current_session)
                if status:
                    st.json({
                        "status": status.get("status"),
                        "total_scenes": status.get("total_scenes"),
                        "completed_scenes": status.get("completed_scenes"),
                        "errors": len(status.get("errors", []))
                    })
            except:
                st.error("Could not fetch session details")
        else:
            st.info("No active session")
        
        # Show available models info
        if st.session_state.available_models:
            models = st.session_state.available_models
            st.markdown("**🤖 Available Models:**")
            st.json({
                "ai_models": len(models.get("ai_models", {}).get("openrouter", [])),
                "runware_models": len(models.get("image_models", {}).get("runware", [])),
                "together_models": len(models.get("image_models", {}).get("together", [])),
                "openrouter_image_models": len(models.get("image_models", {}).get("openrouter_imgae", []))
            })
    
    # Enhanced session management
    st.markdown("### 🧹 Session Management")
    col_debug1, col_debug2, col_debug3 = st.columns(3)
    
    with col_debug1:
        if st.button("🗑️ Clear All Session Data", type="secondary", use_container_width=True):
            keys_to_clear = ["current_project", "current_session", "navigation_history", "project_creation_result", "example_story", "example_title"]
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            st.session_state.current_page = "Create Story"
            st.session_state.navigation_history = ["Create Story"]
            st.success("✅ All session data cleared!")
            time.sleep(1)
            st.rerun()
    
    with col_debug2:
        if st.button("🔄 Clear Cache", use_container_width=True):
            st.cache_data.clear()
            st.success("✅ Cache cleared!")
            time.sleep(1)
            st.rerun()
    
    with col_debug3:
        if st.button("🌐 Test Backend", use_container_width=True):
            health = check_backend_health()
            if health["healthy"]:
                st.success("✅ Backend is healthy!")
                if "data" in health:
                    st.json(health["data"])
            else:
                st.error(f"❌ Backend error: {health['error']}")