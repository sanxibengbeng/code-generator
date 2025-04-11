import unittest
import io
from uicodegen.utils.code_extractor import extract_code_from_text

class TestExtractCode(unittest.TestCase):
    
    def test_extract_code_from_text(self):
        # Test with complete text containing all sections
        test_text = """
Here's the code for your UI:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Test</title>
</head>
<body>
    <h1>Hello World</h1>
</body>
</html>
```

```css
body {
    background-color: #f0f0f0;
}
h1 {
    color: blue;
}
```

```javascript
document.addEventListener('DOMContentLoaded', function() {
    console.log('Page loaded');
});
```

Hope this helps!
"""
        
        # Create a debug file for testing
        debug_file = io.StringIO()
        
        # Extract code
        html, css, js = extract_code_from_text(test_text, debug_file)
        
        # Check extracted code
        self.assertEqual(html.strip(), """<!DOCTYPE html>
<html>
<head>
    <title>Test</title>
</head>
<body>
    <h1>Hello World</h1>
</body>
</html>""")
        
        self.assertEqual(css.strip(), """body {
    background-color: #f0f0f0;
}
h1 {
    color: blue;
}""")
        
        self.assertEqual(js.strip(), """document.addEventListener('DOMContentLoaded', function() {
    console.log('Page loaded');
});""")
        
        # Check debug output
        debug_output = debug_file.getvalue()
        self.assertIn("Found HTML code", debug_output)
        self.assertIn("Found CSS code", debug_output)
        self.assertIn("Found JavaScript code", debug_output)
    
    def test_extract_code_from_text_missing_sections(self):
        # Test with text missing some sections
        test_text = """
Here's the code for your UI:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Test</title>
</head>
<body>
    <h1>Hello World</h1>
</body>
</html>
```

Sorry, I couldn't create CSS or JavaScript for this simple example.
"""
        
        # Create a debug file for testing
        debug_file = io.StringIO()
        
        # Extract code
        html, css, js = extract_code_from_text(test_text, debug_file)
        
        # Check extracted code
        self.assertEqual(html.strip(), """<!DOCTYPE html>
<html>
<head>
    <title>Test</title>
</head>
<body>
    <h1>Hello World</h1>
</body>
</html>""")
        
        self.assertEqual(css, "")
        self.assertEqual(js, "")
        
        # Check debug output
        debug_output = debug_file.getvalue()
        self.assertIn("Found HTML code", debug_output)
        self.assertIn("No CSS code found", debug_output)
        self.assertIn("No JavaScript code found", debug_output)

if __name__ == '__main__':
    unittest.main()
