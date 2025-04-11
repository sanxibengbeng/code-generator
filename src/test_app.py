import unittest
import os
import json
import tempfile
from unittest.mock import patch, MagicMock
from app import app, save_generated_files, extract_code_from_text

class TestApp(unittest.TestCase):
    
    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()
        
        # Create temporary directories for testing
        self.temp_upload_dir = tempfile.mkdtemp()
        self.temp_generated_dir = tempfile.mkdtemp()
        
        # Override app config with temp directories
        app.config['UPLOAD_FOLDER'] = self.temp_upload_dir
        app.config['GENERATED_FOLDER'] = self.temp_generated_dir
    
    def tearDown(self):
        # Clean up temp directories
        import shutil
        shutil.rmtree(self.temp_upload_dir)
        shutil.rmtree(self.temp_generated_dir)
    
    def test_extract_code_from_text(self):
        # Test with well-formatted text
        test_text = """
        Here's the code:
        
        ```html
        <html><body>Test HTML</body></html>
        ```
        
        ```css
        body { color: red; }
        ```
        
        ```javascript
        console.log('test');
        ```
        """
        
        html, css, js = extract_code_from_text(test_text)
        
        self.assertEqual(html, "<html><body>Test HTML</body></html>")
        self.assertEqual(css, "body { color: red; }")
        self.assertEqual(js, "console.log('test');")
    
    def test_extract_code_from_text_missing_sections(self):
        # Test with missing sections
        test_text = """
        Here's the code:
        
        ```html
        <html><body>Test HTML</body></html>
        ```
        
        No CSS provided.
        
        ```javascript
        console.log('test');
        ```
        """
        
        html, css, js = extract_code_from_text(test_text)
        
        self.assertEqual(html, "<html><body>Test HTML</body></html>")
        self.assertEqual(css, "")
        self.assertEqual(js, "console.log('test');")
    
    @patch('app.session_manager')
    def test_save_generated_files(self, mock_session_manager):
        # Mock the session manager's get_generated_path method
        mock_session_manager.get_generated_path.side_effect = lambda session_id, filename: os.path.join(self.temp_generated_dir, filename)
        
        # Test saving files
        html_content = "<html><body>Test</body></html>"
        css_content = "body { color: blue; }"
        js_content = "console.log('Hello');"
        
        file_paths = save_generated_files("test-session", html_content, css_content, js_content)
        
        # Check that files were created with correct content
        with open(file_paths['html'], 'r') as f:
            self.assertEqual(f.read(), html_content)
        
        with open(file_paths['css'], 'r') as f:
            self.assertEqual(f.read(), css_content)
        
        with open(file_paths['js'], 'r') as f:
            self.assertEqual(f.read(), js_content)

if __name__ == '__main__':
    unittest.main()
