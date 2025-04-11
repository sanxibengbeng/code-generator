import unittest
import os
import time
import tempfile
import shutil
from uicodegen.core.session_manager import SessionManager

class TestSessionManager(unittest.TestCase):
    
    def setUp(self):
        # Create temporary directories for testing
        self.temp_upload_dir = tempfile.mkdtemp()
        self.temp_generated_dir = tempfile.mkdtemp()
        
        # Initialize session manager with temp directories
        self.session_manager = SessionManager(
            upload_base_dir=self.temp_upload_dir,
            generated_base_dir=self.temp_generated_dir
        )
    
    def tearDown(self):
        # Clean up temp directories
        shutil.rmtree(self.temp_upload_dir, ignore_errors=True)
        shutil.rmtree(self.temp_generated_dir, ignore_errors=True)
    
    def test_create_session(self):
        # Test creating a new session
        session_id = self.session_manager.create_session()
        
        # Check that session was created
        self.assertIn(session_id, self.session_manager.sessions)
        
        # Check that directories were created
        upload_dir = os.path.join(self.temp_upload_dir, session_id)
        generated_dir = os.path.join(self.temp_generated_dir, session_id)
        self.assertTrue(os.path.exists(upload_dir))
        self.assertTrue(os.path.exists(generated_dir))
        
        # Check that status was initialized
        status = self.session_manager.get_session_status(session_id)
        self.assertEqual(status['current_task'], 'Initialized')
        self.assertEqual(status['progress_percentage'], 0)
    
    def test_update_session_status(self):
        # Create a session
        session_id = self.session_manager.create_session()
        
        # Update status
        self.session_manager.update_session_status(
            session_id,
            current_task='Testing',
            progress_percentage=50,
            is_processing=True
        )
        
        # Check that status was updated
        status = self.session_manager.get_session_status(session_id)
        self.assertEqual(status['current_task'], 'Testing')
        self.assertEqual(status['progress_percentage'], 50)
        self.assertTrue(status['is_processing'])
        
        # Try updating with invalid key (should be ignored)
        self.session_manager.update_session_status(
            session_id,
            invalid_key='This should be ignored'
        )
        
        # Check that invalid key was not added
        self.assertNotIn('invalid_key', self.session_manager.get_session_status(session_id))
    
    def test_get_file_paths(self):
        # Create a session
        session_id = self.session_manager.create_session()
        
        # Get file paths
        upload_path = self.session_manager.get_upload_path(session_id, 'test.jpg')
        generated_path = self.session_manager.get_generated_path(session_id, 'index.html')
        
        # Check paths
        expected_upload_path = os.path.join(self.temp_upload_dir, session_id, 'test.jpg')
        expected_generated_path = os.path.join(self.temp_generated_dir, session_id, 'index.html')
        self.assertEqual(upload_path, expected_upload_path)
        self.assertEqual(generated_path, expected_generated_path)
    
    def test_nonexistent_session(self):
        # Test with nonexistent session ID
        status = self.session_manager.get_session_status('nonexistent')
        self.assertIsNone(status)
        
        upload_path = self.session_manager.get_upload_path('nonexistent', 'test.jpg')
        self.assertIsNone(upload_path)
        
        generated_path = self.session_manager.get_generated_path('nonexistent', 'index.html')
        self.assertIsNone(generated_path)
    
    def test_cleanup_old_sessions(self):
        # Create sessions
        session_id1 = self.session_manager.create_session()
        session_id2 = self.session_manager.create_session()
        
        # Manually set created_at for first session to be old
        self.session_manager.sessions[session_id1]['created_at'] = time.time() - 25 * 3600  # 25 hours ago
        
        # Run cleanup (24 hour max age)
        self.session_manager.cleanup_old_sessions(max_age_hours=24)
        
        # Check that old session was removed but new one remains
        self.assertNotIn(session_id1, self.session_manager.sessions)
        self.assertIn(session_id2, self.session_manager.sessions)

if __name__ == '__main__':
    unittest.main()
