import streamlit as st
import requests
import time
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

# Initialize Session State
def init_session_state():
    """Initialize all session state variables"""
    defaults = {
        "dark_theme": True,
        "available_models": None,
        "current_project": None,
        "current_session": None,
        "current_page": "Create Story",
        "navigation_history": ["Create Story"],
        "project_created": False,
        "project_creation_result": None,
        "last_refresh": None
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# CSS Themes
def get_theme_css():
    """Return CSS for light or dark theme, wrapped properly in <style> tags."""
    base_css = """
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .stApp { font-family: 'Inter', sans-serif !important; }

    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 25%, #f093fb 50%, #f5576c 75%, #4facfe 100%);
        color: white;
        padding: 3rem 2rem;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 20px 40px rgba(102,126,234,0.3);
    }
    """

    light_css = """
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
    """

    dark_css = """
    .stApp { background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%); color: #fff; }
    """

    theme_css = dark_css if st.session_state.get("dark_theme", False) else light_css
    return f"<style>{base_css + theme_css}</style>"


st.markdown(get_theme_css(), unsafe_allow_html=True)

# API Functions
@st.cache_data(ttl=60)
def check_backend_health() -> Dict:
    """Check backend health status"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        return {"healthy": response.status_code == 200, "data": response.json() if response.status_code == 200 else None}
    except Exception as e:
        return {"healthy": False, "error": str(e)}

@st.cache_data(ttl=300)
def load_models() -> Optional[Dict]:
    """Load available AI models"""
    try:
        response = requests.get(f"{API_BASE_URL}/models", timeout=30)
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        st.error(f"Failed to load models: {str(e)}")
        return None

def api_request(endpoint: str, method: str = "GET", data: Dict = None, timeout: int = 30) -> Optional[Dict]:
    """Generic API request handler with improved error handling"""
    try:
        # Ensure endpoint doesn't start with /
        if endpoint.startswith('/'):
            endpoint = endpoint[1:]
            
        url = f"{API_BASE_URL}/{endpoint}"
        
        if method == "GET":
            response = requests.get(url, timeout=timeout)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=timeout)
        elif method == "DELETE":
            response = requests.delete(url, timeout=timeout)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            st.error(f"Resource not found: {endpoint}")
            return None
        else:
            st.error(f"Request failed: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        st.error("Request timed out. Please try again.")
        return None
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to the backend. Please check if the server is running.")
        return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

# Navigation Functions
def navigate_to(page: str):
    """Navigate to a different page"""
    if page != st.session_state.current_page:
        st.session_state.navigation_history.append(st.session_state.current_page)
        st.session_state.current_page = page
        st.rerun()

def reset_project():
    """Reset session state for a new project"""
    st.session_state.current_project = None
    st.session_state.current_session = None
    st.session_state.project_created = False
    st.session_state.project_creation_result = None
    navigate_to("Create Story")

# Load models on startup
if not st.session_state.available_models:
    with st.spinner("Loading models..."):
        st.session_state.available_models = load_models()

# Main Header
st.markdown("""
<div class="main-header">
    <h1>🎬 Story to Image Generator</h1>
    <p>Transform your stories into stunning AI-generated images</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    # Theme toggle
    if st.button(f"{'🌙' if not st.session_state.dark_theme else '☀️'} Toggle Theme"):
        st.session_state.dark_theme = not st.session_state.dark_theme
        st.rerun()
    
    st.markdown("---")
    
    # Backend health check
    health = check_backend_health()
    if health["healthy"]:
        st.success("🟢 Backend Online")
        if health.get("data"):
            col1, col2 = st.columns(2)
            col1.metric("Sessions", health["data"].get('active_sessions', 0))
            col2.metric("Projects", health["data"].get('total_projects', 0))
    else:
        st.error(f"🔴 Backend Offline: {health.get('error', 'Unknown error')}")
        st.warning("Please ensure the backend server is running on http://localhost:8000")
    
    st.markdown("---")
    st.markdown("### 🧭 Navigation")
    
    # Navigation buttons
    pages_list = [
        ("🎭 Create Story", "Create Story"),
        ("🎨 Generate Images", "Generate Images"),
        ("📊 Monitor Progress", "Monitor Progress"),
        ("📁 My Projects", "My Projects")
    ]
    
    for display, key in pages_list:
        button_type = "primary" if key == st.session_state.current_page else "secondary"
        if st.button(display, key=f"nav_{key}", use_container_width=True, type=button_type):
            navigate_to(key)
    
    # Current project info
    if st.session_state.current_project:
        st.markdown("---")
        st.markdown("### 📋 Current Project")
        project = st.session_state.current_project
        project_id = project.get('project_id', 'Unknown')
        word_count = project.get('analysis', {}).get('word_count', 'N/A')
        recommended_scenes = project.get('analysis', {}).get('recommended_scenes', 'N/A')
        
        st.info(f"""
        **ID:** {project_id[:20]}...  
        **Words:** {word_count}  
        **Scenes:** {recommended_scenes}
        """)
        
        if st.button("🗑️ Clear Project", use_container_width=True):
            st.session_state.current_project = None
            st.rerun()
    
    # Quick actions
    st.markdown("---")
    if st.button("🆕 New Project", use_container_width=True):
        reset_project()

# Page Functions
def create_story_page():
    """Create Story page"""
    st.header("🎭 Create New Story Project")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.form("script_form"):
            title = st.text_input("📝 Project Title*", placeholder="Enter a descriptive title")
            script = st.text_area("📖 Story Script*", height=300, 
                                 placeholder="Enter your story here...")
            
            if script:
                word_count = len(script.split())
                st.caption(f"📊 {word_count} words | {len(script)} characters")
            
            submitted = st.form_submit_button("🔍 Analyze & Create Project", type="primary")
            
            if submitted:
                if not title.strip() or not script.strip():
                    st.error("❌ Please provide both title and script")
                elif len(script.split()) < 10:
                    st.error("❌ Script too short (minimum 10 words)")
                else:
                    with st.spinner("🔍 Analyzing script..."):
                        result = api_request("analyze-script", "POST", 
                                           {"script": script.strip(), "title": title.strip()})
                    
                    if result:
                        st.session_state.current_project = result
                        st.session_state.project_creation_result = result
                        
                        # ✅ Save analysis summary for later
                        analysis = result.get("analysis", {})
                        st.session_state.analysis_summary = {
                            "Word Count": analysis.get("word_count", 0),
                            "Recommended Scenes": analysis.get("recommended_scenes", 4),
                            "Estimated Time": f"{analysis.get('estimated_duration_minutes', 0)} min"
                        }

                        st.success(f"🎉 Project created! Word count: {analysis.get('word_count', 0)}")
                        time.sleep(1)
                        navigate_to("Generate Images")
    
    with col2:
        st.markdown("### 💡 Tips")
        st.info("""
        **Visual Descriptions:**
        • Use rich, descriptive language  
        • Include colors and atmosphere  
        • Describe characters and settings  

        **Length Guide:**  
        • Short: 50-100 words (2-4 scenes)  
        • Medium: 100-300 words (4-8 scenes)  
        • Long: 300+ words (8+ scenes)  
        """)

def generate_images_page():
    """Generate Images page"""
    st.header("🎨 Generate Images from Story")
    
    if not st.session_state.current_project:
        st.warning("⚠️ No project selected")
        col1, col2 = st.columns(2)
        if col1.button("🆕 Create New Project", use_container_width=True):
            navigate_to("Create Story")
        if col2.button("📁 View Projects", use_container_width=True):
            navigate_to("My Projects")
        return
    
    project = st.session_state.current_project
    project_id = project.get("project_id", "Unknown")

    # ✅ Show analysis summary
    st.markdown("#### 📊 Project Analysis")
    summary = st.session_state.get("analysis_summary", {})
    if summary:
        cols = st.columns(len(summary))
        for idx, (label, value) in enumerate(summary.items()):
            cols[idx].metric(label, value)
    else:
        st.info("No analysis summary available.")

    st.success(f"📋 Project: {project_id}")
    
    models = st.session_state.available_models
    if not models:
        st.error("❌ Failed to load models. Please refresh the page.")
        if st.button("🔄 Refresh Models"):
            st.session_state.available_models = None
            st.rerun()
        return
    
    st.markdown("### ⚙️ Generation Settings")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        ai_models = models.get("ai_models", {}).get("Openai", ["fallback"])
        ai_model = st.selectbox("AI Model:", ai_models, key="ai_model_select")
    
    with col2:
        image_provider = st.selectbox("Image Provider:", ["runware", "together"], key="image_provider_select")
        provider_models = models.get("image_models", {}).get(image_provider, [])
        
        if not provider_models:
            st.error(f"❌ No {image_provider} models available")
            return
        
        image_model = st.selectbox(f"{image_provider.title()} Model:", provider_models, key="image_model_select")
    
    with col3:
        media_type = st.selectbox("Visual Style:", 
                                 ["cinematic", "cartoon", "realistic", "artistic"], key="media_type_select")
    
    with col4:
        recommended = project.get("analysis", {}).get("recommended_scenes", 4)
        num_scenes = st.number_input("Number of scenes:", 
                                    min_value=1, max_value=50, value=recommended, key="num_scenes_input")
    
    if st.button("🚀 Generate Scene Previews", use_container_width=True, type="primary"):
        payload = {
            "project_id": project.get("project_id"),
            "num_scenes": num_scenes,
            "media_type": media_type,
            "ai_provider": "Openai",
            "ai_model": ai_model,
            "image_provider": image_provider,
            "image_model": image_model,
        }
        
        with st.spinner("🚀 Starting generation..."):
            result = api_request("generate-previews", "POST", payload, timeout=120)
        
        if result:
            st.session_state.current_session = result.get("session_id")
            session_id = result.get("session_id", "Unknown")
            st.success(f"🎉 Generation started! Session: {session_id}")
            time.sleep(1)
            navigate_to("Monitor Progress")

def monitor_progress_page():
    """Monitor Progress page"""
    st.header("📊 Monitor Generation Progress")
    
    session_id = st.text_input("🔍 Session ID:", 
                              value=st.session_state.current_session or "",
                              placeholder="session_abcd1234")
    
    if not session_id:
        st.info("💡 Enter a session ID to monitor progress")
        return
    
    col1, col2 = st.columns(2)
    auto_refresh = col1.checkbox("🔄 Auto-refresh", value=True, key="auto_refresh_checkbox")
    manual_refresh = col2.button("📊 Check Status", key="manual_refresh_button")
    
    if manual_refresh or auto_refresh:
        status = api_request(f"generation-status/{session_id}")
        
        if not status:
            st.error("❌ Session not found or backend error")
            return
        
        # Progress bar
        total_scenes = max(status.get("total_scenes", 1), 1)
        completed_scenes = status.get("completed_scenes", 0)
        progress = completed_scenes / total_scenes
        st.progress(progress, text=f"Progress: {completed_scenes}/{total_scenes} scenes")
        
        # Status metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Status", status.get('status', 'Unknown').title())
        col2.metric("Progress", f"{int(progress*100)}%")
        col3.metric("Total Scenes", total_scenes)
        col4.metric("Errors", len(status.get("errors", [])))
        
        # Display previews
        if status.get("previews"):
            st.markdown("---")
            st.subheader("🖼️ Generated Previews")
            
            sorted_previews = sorted(status["previews"], key=lambda x: x.get("scene_number", 0))
            approvals = {}
            
            for i, preview in enumerate(sorted_previews):
                if i % 2 == 0:
                    cols = st.columns(2)
                
                with cols[i % 2]:
                    scene_number = preview.get('scene_number', i+1)
                    scene_title = preview.get('scene_title', f'Scene {scene_number}')
                    st.markdown(f"### 🎬 Scene {scene_number}: {scene_title}")
                    
                    if preview.get("preview_url"):
                        try:
                            st.image(preview["preview_url"], use_container_width=True)
                            approvals[str(scene_number)] = st.checkbox(
                                f"✅ Save Scene {scene_number}", 
                                value=True,
                                key=f"approve_{scene_number}_{session_id}_{i}"
                            )
                        except Exception as e:
                            st.error(f"❌ Failed to load image: {str(e)}")
                            approvals[str(scene_number)] = False
                    else:
                        error_msg = preview.get('error', 'Unknown error')
                        st.error(f"❌ Generation failed: {error_msg}")
                        approvals[str(scene_number)] = False
            
            # Save approved scenes
            if status.get("status") in ["previewing", "completed"]:
                st.markdown("---")
                selected_count = sum(1 for approved in approvals.values() if approved)
                st.info(f"📊 {selected_count} scenes selected for saving")
                
                if st.button("💾 Save Selected Scenes", disabled=selected_count == 0, 
                           use_container_width=True, type="primary", key="save_scenes_button"):
                    with st.spinner("💾 Saving scenes..."):
                        result = api_request("approve-previews", "POST", 
                                           {"session_id": session_id, "scene_approvals": approvals})
                    
                    if result:
                        saved_count = result.get('saved_images', selected_count)
                        st.success(f"🎉 Saved {saved_count} images!")
                        time.sleep(1)
                        navigate_to("My Projects")
        
        # Auto-refresh logic
        if auto_refresh and status.get("status") == "generating":
            # Add a small delay to prevent too frequent refreshes
            current_time = time.time()
            if (st.session_state.last_refresh is None or 
                current_time - st.session_state.last_refresh > POLLING_INTERVAL):
                st.session_state.last_refresh = current_time
                time.sleep(POLLING_INTERVAL)
                st.rerun()

def my_projects_page():
    """My Projects page - Fixed version"""
    st.header("📁 My Projects")
    
    projects = api_request("projects")
    
    if not projects or not projects.get("projects"):
        st.info("💡 No projects found")
        if st.button("🆕 Create New Project", use_container_width=True):
            navigate_to("Create Story")
        return
    
    project_list = projects["projects"]
    st.success(f"📊 Found {len(project_list)} projects")
    
    # Search and sort
    col1, col2 = st.columns([2, 1])
    search_term = col1.text_input("🔍 Search:", placeholder="Enter project ID", key="search_projects")
    sort_by = col2.selectbox("Sort by:", ["Newest First", "Oldest First", "Most Words"], key="sort_projects")
    
    # Filter projects
    if search_term:
        filtered = [p for p in project_list if search_term.lower() in p.get('project_id', '').lower()]
    else:
        filtered = project_list
    
    # Sort projects
    if sort_by == "Newest First":
        filtered.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    elif sort_by == "Oldest First":
        filtered.sort(key=lambda x: x.get('created_at', ''))
    elif sort_by == "Most Words":
        filtered.sort(key=lambda x: x.get('analysis', {}).get('word_count', 0), reverse=True)
    
    # Display projects
    for i, project in enumerate(filtered[:10]):  # Show max 10 projects
        project_id = project.get('project_id', 'Unknown')
        word_count = project.get('analysis', {}).get('word_count', 0)
        
        with st.expander(f"📄 {project_id} - {word_count} words", expanded=(i < 2)):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                created_at = project.get('created_at', 'Unknown')
                if created_at != 'Unknown' and 'T' in created_at:
                    created_at = created_at[:19].replace('T', ' ')
                
                recommended_scenes = project.get('analysis', {}).get('recommended_scenes', 'N/A')
                estimated_duration = project.get('analysis', {}).get('estimated_duration_minutes', 'N/A')
                
                st.markdown(f"""
                📅 **Created:** {created_at}  
                📊 **Word Count:** {word_count}  
                🎬 **Recommended Scenes:** {recommended_scenes}  
                ⏱️ **Est. Duration:** {estimated_duration} min
                """)
                
                # Load project details with proper error handling
                try:
                    details = api_request(f"projects/{project_id}")
                    if details and details.get('images'):
                        image_count = len(details['images'])
                        st.success(f"🖼️ {image_count} images generated")
                        
                        # Show thumbnails
                        images_to_show = details['images'][:4]
                        if images_to_show:
                            img_cols = st.columns(min(4, len(images_to_show)))
                            for idx, img_path in enumerate(images_to_show):
                                with img_cols[idx]:
                                    try:
                                        full_img_url = f"{API_BASE_URL}{img_path}"
                                        st.image(full_img_url, use_container_width=True)
                                    except Exception as e:
                                        st.error("❌ Image load failed")
                    else:
                        st.info("📝 No images generated yet")
                        
                except Exception as e:
                    st.warning(f"⚠️ Could not load project details: {str(e)}")
            
            with col2:
                if st.button("🎨 Generate Images", key=f"gen_{project_id}_{i}", 
                           use_container_width=True):
                    st.session_state.current_project = project
                    navigate_to("Generate Images")
                
                if st.button("📋 Use Project", key=f"use_{project_id}_{i}", 
                           use_container_width=True):
                    st.session_state.current_project = project
                    st.rerun()
# Main Router
pages = {
    "Create Story": create_story_page,
    "Generate Images": generate_images_page,
    "Monitor Progress": monitor_progress_page,
    "My Projects": my_projects_page
}

current_page = st.session_state.current_page
if current_page in pages:
    pages[current_page]()
else:
    st.error(f"Page '{current_page}' not found")
    navigate_to("Create Story")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <h4>🎬 Story to Image Generator</h4>
    <p>Powered by Openai, Runware & Together AI</p>
</div>
""", unsafe_allow_html=True)