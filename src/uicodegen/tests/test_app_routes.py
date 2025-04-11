import unittest
import os
import json
import tempfile
from unittest.mock import patch, MagicMock
import sys

# Mock boto3 and botocore before importing app
sys.modules['boto3'] = MagicMock()
sys.modules['botocore'] = MagicMock()
sys.modules['botocore.config'] = MagicMock()

# Import the app after mocking dependencies
from uicodegen.web.app import create_app
from uicodegen.core.session_manager import SessionManager

class TestAppRoutes(unittest.TestCase):
    
    def setUp(self):
        # Create temporary directories for testing
        self.temp_upload_dir = tempfile.mkdtemp()
        self.temp_generated_dir = tempfile.mkdtemp()
        
        # Create app with test config
        self.app = create_app({
            'TESTING': True,
            'UPLOAD_FOLDER': self.temp_upload_dir,
            'GENERATED_FOLDER': self.temp_generated_dir
        })
        
        self.client = self.app.test_client()
        
        # Get session manager from app
        self.session_manager = None
        for rule in self.app.url_map.iter_rules():
            if rule.endpoint == 'get_progress':
                view_func = self.app.view_functions[rule.endpoint]
                # Extract session_manager from closure
                self.session_manager = view_func.__closure__[1].cell_contents
                break
    
    def tearDown(self):
        # Clean up temp directories
        import shutil
        shutil.rmtree(self.temp_upload_dir, ignore_errors=True)
        shutil.rmtree(self.temp_generated_dir, ignore_errors=True)
    
    @patch('uicodegen.web.routes.render_template')
    def test_index_route(self, mock_render):
        # Test the index route
        mock_render.return_value = "Mocked template"
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        mock_render.assert_called_once()
        # Check that models are passed to the template
        args, kwargs = mock_render.call_args
        self.assertIn('models', kwargs)
    
    def test_upload_route_no_file(self):
        # Test upload route with no file
        response = self.client.post('/upload')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'No file part')
    
    def test_upload_route_empty_filename(self):
        # Test upload route with empty filename
        response = self.client.post('/upload', data={
            'file': (b'', '')
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'No selected file')
    
    @patch('uicodegen.web.routes.threading.Thread')
    def test_upload_route_success(self, mock_thread):
        # Test successful upload
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        with open(__file__, 'rb') as test_file:
            response = self.client.post('/upload', data={
                'file': (test_file, 'test.py'),
                'model': 'claude-3-7-sonnet',
                'streaming': 'true'
            })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('message', data)
        self.assertEqual(data['message'], 'Processing started')
        self.assertIn('session_id', data)
        self.assertIn('model', data)
        self.assertEqual(data['model'], 'claude-3-7-sonnet')
        self.assertIn('streaming', data)
        self.assertTrue(data['streaming'])
        
        # Check that thread was started
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()
    
    def test_progress_route_invalid_session(self):
        # Test progress route with invalid session ID
        response = self.client.get('/progress/invalid-session-id')
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Session not found')
    
    def test_progress_route_valid_session(self):
        # Create a test session
        session_id = self.session_manager.create_session()
        self.session_manager.update_session_status(
            session_id,
            current_task="Test task",
            progress_percentage=50
        )
        
        # Test progress route with valid session ID
        response = self.client.get(f'/progress/{session_id}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['current_task'], "Test task")
        self.assertEqual(data['progress_percentage'], 50)
    
    def test_result_route_invalid_session(self):
        # Test result route with invalid session ID
        response = self.client.get('/result/invalid-session-id')
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Session not found')
    
    def test_result_route_incomplete_processing(self):
        # Create a test session with incomplete processing
        session_id = self.session_manager.create_session()
        self.session_manager.update_session_status(
            session_id,
            processing_complete=False
        )
        
        # Test result route with incomplete processing
        response = self.client.get(f'/result/{session_id}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Processing not complete')
    
    def test_result_route_complete_processing(self):
        # Create a test session with complete processing
        session_id = self.session_manager.create_session()
        self.session_manager.update_session_status(
            session_id,
            processing_complete=True,
            input_tokens=100,
            output_tokens=200,
            processing_time=1.5,
            streaming_chunks=10,
            use_streaming=True
        )
        
        # Test result route with complete processing
        response = self.client.get(f'/result/{session_id}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('html_path', data)
        self.assertIn('css_path', data)
        self.assertIn('js_path', data)
        self.assertIn('metrics', data)
        self.assertEqual(data['metrics']['input_tokens'], 100)
        self.assertEqual(data['metrics']['output_tokens'], 200)
        self.assertEqual(data['metrics']['processing_time'], 1.5)
        self.assertEqual(data['metrics']['streaming_chunks'], 10)

if __name__ == '__main__':
    unittest.main()
