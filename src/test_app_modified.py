import unittest
import os
import json
import tempfile
from unittest.mock import patch, MagicMock

# Mock boto3 and botocore before importing app
import sys
sys.modules['boto3'] = MagicMock()
sys.modules['botocore'] = MagicMock()
sys.modules['botocore.config'] = MagicMock()

from app import extract_code_from_text

class TestAppFunctions(unittest.TestCase):
    
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

if __name__ == '__main__':
    unittest.main()
