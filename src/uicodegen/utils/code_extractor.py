"""
Utility for extracting code blocks from AI model responses
"""
import re

def extract_code_from_text(text, debug_file=None):
    """
    Extract HTML, CSS, and JavaScript code blocks from text
    
    Args:
        text (str): Text containing code blocks
        debug_file (file): Optional file-like object for debug logging
        
    Returns:
        tuple: (html_code, css_code, js_code)
    """
    # Initialize empty code blocks
    html_code = ""
    css_code = ""
    js_code = ""
    
    # Log the input text length if debug file is provided
    if debug_file:
        debug_file.write(f"Input text length: {len(text)}\n")
        debug_file.write(f"First 100 chars: {text[:100]}\n\n")
    
    # Extract HTML code
    html_pattern = r"```html\s*(.*?)```"
    html_matches = re.findall(html_pattern, text, re.DOTALL)
    
    if html_matches:
        html_code = html_matches[0].strip()
        if debug_file:
            debug_file.write(f"Found HTML code ({len(html_code)} chars)\n")
    else:
        if debug_file:
            debug_file.write("No HTML code found\n")
    
    # Extract CSS code
    css_pattern = r"```css\s*(.*?)```"
    css_matches = re.findall(css_pattern, text, re.DOTALL)
    
    if css_matches:
        css_code = css_matches[0].strip()
        if debug_file:
            debug_file.write(f"Found CSS code ({len(css_code)} chars)\n")
    else:
        if debug_file:
            debug_file.write("No CSS code found\n")
    
    # Extract JavaScript code
    js_pattern = r"```javascript\s*(.*?)```"
    js_matches = re.findall(js_pattern, text, re.DOTALL)
    
    if js_matches:
        js_code = js_matches[0].strip()
        if debug_file:
            debug_file.write(f"Found JavaScript code ({len(js_code)} chars)\n")
    else:
        # Try alternative pattern for JavaScript
        js_pattern = r"```js\s*(.*?)```"
        js_matches = re.findall(js_pattern, text, re.DOTALL)
        
        if js_matches:
            js_code = js_matches[0].strip()
            if debug_file:
                debug_file.write(f"Found JavaScript code using alternative pattern ({len(js_code)} chars)\n")
        else:
            if debug_file:
                debug_file.write("No JavaScript code found\n")
    
    return html_code, css_code, js_code
