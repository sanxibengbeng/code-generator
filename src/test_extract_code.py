import unittest
import re

def extract_code_from_text(full_text, debug_file=None):
    """Extract HTML, CSS, and JavaScript code from the text response"""
    # Initialize code blocks
    html_code = ""
    css_code = ""
    js_code = ""
    
    if debug_file:
        debug_file.write(f"Extracting code from text of length: {len(full_text)}\n")
    
    # Extract HTML code
    html_match = re.search(r'```html\s*(.*?)\s*```', full_text, re.DOTALL)
    if html_match:
        html_code = html_match.group(1).strip()
        if debug_file:
            debug_file.write(f"Found HTML code of length: {len(html_code)}\n")
    elif debug_file:
        debug_file.write("No HTML code found\n")
    
    # Extract CSS code
    css_match = re.search(r'```css\s*(.*?)\s*```', full_text, re.DOTALL)
    if css_match:
        css_code = css_match.group(1).strip()
        if debug_file:
            debug_file.write(f"Found CSS code of length: {len(css_code)}\n")
    elif debug_file:
        debug_file.write("No CSS code found\n")
    
    # Extract JavaScript code
    js_match = re.search(r'```javascript\s*(.*?)\s*```', full_text, re.DOTALL)
    if js_match:
        js_code = js_match.group(1).strip()
        if debug_file:
            debug_file.write(f"Found JavaScript code of length: {len(js_code)}\n")
    elif debug_file:
        debug_file.write("No JavaScript code found\n")
    
    return html_code, css_code, js_code

class TestExtractCode(unittest.TestCase):
    
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
