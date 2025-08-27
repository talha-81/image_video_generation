"""Models package for the Story to Image Generator API."""

from .schemas import (
    ScriptAnalysis,
    ScriptRequest, 
    ProjectInfo,
    ScenePrompt,
    GenerationRequest,
    RegenerationRequest,
    PreviewImage,
    GenerationSession,
    ApprovalRequest
)

from .session_manager import (
    get_session,
    set_session,
    delete_session,
    count_sessions,
    all_sessions,
    cleanup_completed_sessions
)

__all__ = [
    # Schemas
    'ScriptAnalysis',
    'ScriptRequest',
    'ProjectInfo', 
    'ScenePrompt',
    'GenerationRequest',
    'RegenerationRequest',
    'PreviewImage',
    'GenerationSession',
    'ApprovalRequest',
    # Session management
    'get_session',
    'set_session', 
    'delete_session',
    'count_sessions',
    'all_sessions',
    'cleanup_completed_sessions'
]