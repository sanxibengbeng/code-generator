"""
Session manager for handling user sessions and file paths
"""
import os
import time
import uuid
import shutil
from datetime import datetime

class SessionManager:
    """
    Manages user sessions, file paths, and status tracking
    """

    def __init__(self, upload_base_dir='uploads', generated_base_dir='generated'):
        """
        Initialize the session manager
        
        Args:
            upload_base_dir (str): Base directory for uploaded files
            generated_base_dir (str): Base directory for generated files
        """
        self.upload_base_dir = upload_base_dir
        self.generated_base_dir = generated_base_dir
        self.sessions = {}

        # Create base directories if they don't exist
        os.makedirs(upload_base_dir, exist_ok=True)
        os.makedirs(generated_base_dir, exist_ok=True)

    def create_session(self):
        """
        Create a new session with a unique ID
        
        Returns:
            str: Session ID
        """
        # Generate a unique session ID
        session_id = str(uuid.uuid4())

        # Create session directories
        upload_dir = os.path.join(self.upload_base_dir, session_id)
        generated_dir = os.path.join(self.generated_base_dir, session_id)

        os.makedirs(upload_dir, exist_ok=True)
        os.makedirs(generated_dir, exist_ok=True)

        # Initialize session status
        self.sessions[session_id] = {
            'created_at': time.time(),
            'current_task': 'Initialized',
            'progress_percentage': 0,
            'is_processing': False,
            'processing_complete': False,
            'error_message': None,
            'input_tokens': 0,
            'output_tokens': 0,
            'processing_time': 0,
            'streaming_chunks': 0,
            'selected_model': None,
            'use_streaming': False,
            'first_token_time': 0,
            'tokens_per_second': 0
        }

        return session_id

    def get_session_status(self, session_id):
        """
        Get the status of a session
        
        Args:
            session_id (str): Session ID
            
        Returns:
            dict: Session status or None if session doesn't exist
        """
        return self.sessions.get(session_id)

    def update_session_status(self, session_id, **kwargs):
        """
        Update the status of a session
        
        Args:
            session_id (str): Session ID
            **kwargs: Key-value pairs to update
            
        Returns:
            bool: True if successful, False if session doesn't exist
        """
        if session_id not in self.sessions:
            return False

        # Update only valid keys
        for key, value in kwargs.items():
            if key in self.sessions[session_id]:
                self.sessions[session_id][key] = value

        # Calculate tokens per second when progress reaches 100%
        if kwargs.get('progress_percentage') == 100:
            session = self.sessions[session_id]
            processing_time = session.get('processing_time', 0)
            output_tokens = session.get('output_tokens', 0)

            # Calculate tokens per second if processing time is available (in milliseconds)
            if processing_time > 0 and output_tokens > 0:
                # Convert processing time from milliseconds to seconds for the calculation
                tokens_per_second = round(output_tokens / processing_time, 2)
                self.sessions[session_id]['tokens_per_second'] = tokens_per_second

        return True

    def get_upload_path(self, session_id, filename):
        """
        Get the path for an uploaded file
        
        Args:
            session_id (str): Session ID
            filename (str): Filename
            
        Returns:
            str: Full path or None if session doesn't exist
        """
        if session_id not in self.sessions:
            return None

        return os.path.join(self.upload_base_dir, session_id, filename)

    def get_generated_path(self, session_id, filename):
        """
        Get the path for a generated file
        
        Args:
            session_id (str): Session ID
            filename (str): Filename
            
        Returns:
            str: Full path or None if session doesn't exist
        """
        if session_id not in self.sessions:
            return None

        return os.path.join(self.generated_base_dir, session_id, filename)

    def cleanup_old_sessions(self, max_age_hours=24):
        """
        Clean up sessions older than the specified age
        
        Args:
            max_age_hours (int): Maximum age in hours
            
        Returns:
            int: Number of sessions cleaned up
        """
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        sessions_to_remove = []

        # Find old sessions
        for session_id, session_data in self.sessions.items():
            if current_time - session_data['created_at'] > max_age_seconds:
                sessions_to_remove.append(session_id)

        # Remove old sessions
        for session_id in sessions_to_remove:
            # Remove session directories
            upload_dir = os.path.join(self.upload_base_dir, session_id)
            generated_dir = os.path.join(self.generated_base_dir, session_id)

            if os.path.exists(upload_dir):
                shutil.rmtree(upload_dir)

            if os.path.exists(generated_dir):
                shutil.rmtree(generated_dir)

            # Remove session from dictionary
            del self.sessions[session_id]

        return len(sessions_to_remove)
