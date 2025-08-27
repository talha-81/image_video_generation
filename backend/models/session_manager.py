from typing import Dict, Optional
from .schemas import GenerationSession

# In-memory session registry
_sessions: Dict[str, GenerationSession] = {}

def get_session(session_id: str) -> Optional[GenerationSession]:
    """Get a session by ID."""
    return _sessions.get(session_id)

def set_session(session: GenerationSession) -> None:
    """Store or update a session."""
    _sessions[session.session_id] = session

def delete_session(session_id: str) -> bool:
    """Delete a session and return True if it existed."""
    return _sessions.pop(session_id, None) is not None

def count_sessions() -> int:
    """Get the total number of active sessions."""
    return len(_sessions)

def all_sessions() -> Dict[str, GenerationSession]:
    """Get all sessions (for debugging)."""
    return _sessions.copy()

def cleanup_completed_sessions() -> int:
    """Remove completed sessions and return count of removed sessions."""
    completed_sessions = [
        session_id for session_id, session in _sessions.items() 
        if session.status in ["completed", "failed"]
    ]
    
    for session_id in completed_sessions:
        del _sessions[session_id]
    
    return len(completed_sessions)