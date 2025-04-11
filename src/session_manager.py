import os
import uuid
import time
import json
from threading import Lock

class SessionManager:
    """
    Manages user sessions for code generation tasks
    """
    def __init__(self, upload_base_dir='uploads', generated_base_dir='generated'):
        self.upload_base_dir = upload_base_dir
        self.generated_base_dir = generated_base_dir
        self.sessions = {}
        self.lock = Lock()
        
        # Ensure base directories exist
        os.makedirs(self.upload_base_dir, exist_ok=True)
        os.makedirs(self.generated_base_dir, exist_ok=True)
    
    def create_session(self):
        """Create a new session with unique ID"""
        with self.lock:
            session_id = str(uuid.uuid4())
            
            # Create session-specific directories
            upload_dir = os.path.join(self.upload_base_dir, session_id)
            generated_dir = os.path.join(self.generated_base_dir, session_id)
            
            os.makedirs(upload_dir, exist_ok=True)
            os.makedirs(generated_dir, exist_ok=True)
            
            # Initialize session data
            self.sessions[session_id] = {
                'created_at': time.time(),
                'upload_dir': upload_dir,
                'generated_dir': generated_dir,
                'status': {
                    'current_task': 'Initialized',
                    'progress_percentage': 0,
                    'is_processing': False,
                    'processing_complete': False,
                    'error_message': None,
                    'selected_model': None,
                    'use_streaming': False,
                    'streaming_chunks': 0,
                    'input_tokens': 0,
                    'output_tokens': 0,
                    'processing_time': 0
                }
            }
            
            return session_id
    
    def get_session(self, session_id):
        """Get session data by ID"""
        return self.sessions.get(session_id)
    
    def update_session_status(self, session_id, **kwargs):
        """Update session status with provided values"""
        if session_id in self.sessions:
            with self.lock:
                for key, value in kwargs.items():
                    if key in self.sessions[session_id]['status']:
                        self.sessions[session_id]['status'][key] = value
    
    def get_session_status(self, session_id):
        """Get current status of a session"""
        if session_id in self.sessions:
            return self.sessions[session_id]['status']
        return None
    
    def get_upload_path(self, session_id, filename):
        """Get path for uploaded file in this session"""
        if session_id in self.sessions:
            return os.path.join(self.sessions[session_id]['upload_dir'], filename)
        return None
    
    def get_generated_path(self, session_id, filename):
        """Get path for generated file in this session"""
        if session_id in self.sessions:
            return os.path.join(self.sessions[session_id]['generated_dir'], filename)
        return None
    
    def cleanup_old_sessions(self, max_age_hours=24):
        """Remove sessions older than max_age_hours"""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        with self.lock:
            for session_id in list(self.sessions.keys()):
                session = self.sessions[session_id]
                if current_time - session['created_at'] > max_age_seconds:
                    # Remove session data
                    self.sessions.pop(session_id, None)
                    
                    # Optionally remove files (uncomment if needed)
                    # import shutil
                    # shutil.rmtree(session['upload_dir'], ignore_errors=True)
                    # shutil.rmtree(session['generated_dir'], ignore_errors=True)
