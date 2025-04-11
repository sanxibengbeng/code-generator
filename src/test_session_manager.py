import unittest
import os
import shutil
import time
from session_manager import SessionManager

class TestSessionManager(unittest.TestCase):
    
    def setUp(self):
        # Create test directories
        self.test_upload_dir = 'test_uploads'
        self.test_generated_dir = 'test_generated'
        
        # Initialize session manager with test directories
        self.session_manager = SessionManager(
            upload_base_dir=self.test_upload_dir,
            generated_base_dir=self.test_generated_dir
        )
    
    def tearDown(self):
        # Clean up test directories
        if os.path.exists(self.test_upload_dir):
            shutil.rmtree(self.test_upload_dir)
        if os.path.exists(self.test_generated_dir):
            shutil.rmtree(self.test_generated_dir)
    
    def test_create_session(self):
        # Test session creation
        session_id = self.session_manager.create_session()
        
        # Verify session was created
        self.assertIn(session_id, self.session_manager.sessions)
        
        # Verify directories were created
        upload_dir = os.path.join(self.test_upload_dir, session_id)
        generated_dir = os.path.join(self.test_generated_dir, session_id)
        self.assertTrue(os.path.exists(upload_dir))
        self.assertTrue(os.path.exists(generated_dir))
        
        # Verify initial status
        status = self.session_manager.get_session_status(session_id)
        self.assertEqual(status['current_task'], 'Initialized')
        self.assertEqual(status['progress_percentage'], 0)
        self.assertFalse(status['is_processing'])
    
    def test_update_session_status(self):
        # Create a session
        session_id = self.session_manager.create_session()
        
        # Update status
        self.session_manager.update_session_status(
            session_id,
            current_task='Processing',
            progress_percentage=50,
            is_processing=True
        )
        
        # Verify status was updated
        status = self.session_manager.get_session_status(session_id)
        self.assertEqual(status['current_task'], 'Processing')
        self.assertEqual(status['progress_percentage'], 50)
        self.assertTrue(status['is_processing'])
    
    def test_get_file_paths(self):
        # Create a session
        session_id = self.session_manager.create_session()
        
        # Get file paths
        upload_path = self.session_manager.get_upload_path(session_id, 'test.jpg')
        generated_path = self.session_manager.get_generated_path(session_id, 'index.html')
        
        # Verify paths are correct
        expected_upload_path = os.path.join(self.test_upload_dir, session_id, 'test.jpg')
        expected_generated_path = os.path.join(self.test_generated_dir, session_id, 'index.html')
        self.assertEqual(upload_path, expected_upload_path)
        self.assertEqual(generated_path, expected_generated_path)
    
    def test_cleanup_old_sessions(self):
        # Create a session
        session_id = self.session_manager.create_session()
        
        # Manually set creation time to be old
        self.session_manager.sessions[session_id]['created_at'] = time.time() - 25 * 3600  # 25 hours ago
        
        # Run cleanup (24 hours max age)
        self.session_manager.cleanup_old_sessions(max_age_hours=24)
        
        # Verify session was removed
        self.assertNotIn(session_id, self.session_manager.sessions)
    
    def test_nonexistent_session(self):
        # Test behavior with nonexistent session ID
        fake_session_id = 'nonexistent-session'
        
        # These should return None, not raise exceptions
        self.assertIsNone(self.session_manager.get_session(fake_session_id))
        self.assertIsNone(self.session_manager.get_session_status(fake_session_id))
        self.assertIsNone(self.session_manager.get_upload_path(fake_session_id, 'test.jpg'))
        self.assertIsNone(self.session_manager.get_generated_path(fake_session_id, 'index.html'))
        
        # This should not raise an exception
        self.session_manager.update_session_status(fake_session_id, current_task='Test')

if __name__ == '__main__':
    unittest.main()
