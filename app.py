import os
import base64
import json
import time
import boto3
import threading
from flask import Flask, request, render_template, jsonify, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder='generated')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
app.config['GENERATED_FOLDER'] = 'generated'

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['GENERATED_FOLDER'], exist_ok=True)

# Global variables for tracking progress
current_task = "Idle"
progress_percentage = 0
is_processing = False
processing_complete = False
error_message = None

# Initialize Bedrock client
bedrock_runtime = boto3.client(
    service_name='bedrock-runtime',
    region_name='us-east-1'
)

def encode_image(image_path):
    """Encode image to base64 string"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def update_progress(task, percentage):
    """Update the global progress variables"""
    global current_task, progress_percentage
    current_task = task
    progress_percentage = percentage

def save_generated_files(html_content, css_content, js_content):
    """Save the generated code to files"""
    file_paths = {}
    
    # Save HTML
    html_path = os.path.join(app.config['GENERATED_FOLDER'], 'index.html')
    with open(html_path, 'w') as f:
        f.write(html_content)
    file_paths['html'] = html_path
    
    # Save CSS
    css_path = os.path.join(app.config['GENERATED_FOLDER'], 'styles.css')
    with open(css_path, 'w') as f:
        f.write(css_content)
    file_paths['css'] = css_path
    
    # Save JS
    js_path = os.path.join(app.config['GENERATED_FOLDER'], 'script.js')
    with open(js_path, 'w') as f:
        f.write(js_content)
    file_paths['js'] = js_path
    
    return file_paths

def process_image(image_path):
    """Process the image with Bedrock Claude 3.7 Sonnet"""
    global is_processing, processing_complete, error_message
    
    try:
        update_progress("Preparing image for processing", 10)
        
        # Encode image to base64
        base64_image = encode_image(image_path)
        
        update_progress("Connecting to AWS Bedrock", 20)
        
        # Prepare the prompt for Claude
        prompt = f"""
        You are an expert web developer. I'm showing you a UI design image. 
        Please convert this design into responsive HTML, CSS, and JavaScript code.
        
        Use Bootstrap 5 for the responsive layout and Vue.js 3 for interactivity.
        Include Font Awesome for icons.
        
        Please provide:
        1. Complete index.html file
        2. Complete styles.css file
        3. Complete script.js file
        
        Make sure the code is clean, well-commented, and follows best practices.
        Make sure the code is the same language as in the picture.
        The website should be fully responsive and match the design as closely as possible.
        
        Return your response in the following format:
        
        ```html
        <!-- Your complete HTML code here -->
        ```
        
        ```css
        /* Your complete CSS code here */
        ```
        
        ```javascript
        // Your complete JavaScript code here
        ```
        """
        
        update_progress("Sending request to Claude 3.7 Sonnet", 30)
        
        # Create the request payload
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": base64_image
                            }
                        }
                    ]
                }
            ]
        }
        
        # Convert the request body to JSON
        request_body_json = json.dumps(request_body)
        
        update_progress("Processing with Claude 3.7 Sonnet", 40)
        
        # Invoke the model
        response = bedrock_runtime.invoke_model(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            body=request_body_json
        )
        
        update_progress("Parsing response", 70)
        
        # Parse the response
        response_body = json.loads(response.get('body').read())
        content = response_body.get('content', [])
        
        # Extract text from the response
        full_text = ""
        for item in content:
            if item.get('type') == 'text':
                full_text += item.get('text', '')
        
        update_progress("Extracting code from response", 80)
        
        # Extract HTML, CSS, and JS code
        html_code = ""
        css_code = ""
        js_code = ""
        
        # Extract HTML
        html_start = full_text.find("```html")
        html_end = full_text.find("```", html_start + 6)
        if html_start != -1 and html_end != -1:
            html_code = full_text[html_start + 6:html_end].strip()
        
        # Extract CSS
        css_start = full_text.find("```css")
        css_end = full_text.find("```", css_start + 6)
        if css_start != -1 and css_end != -1:
            css_code = full_text[css_start + 6:css_end].strip()
        
        # Extract JS
        js_start = full_text.find("```javascript")
        js_end = full_text.find("```", js_start + 14)
        if js_start != -1 and js_end != -1:
            js_code = full_text[js_start + 14:js_end].strip()
        
        update_progress("Saving generated files", 90)
        
        # Save the generated code to files
        file_paths = save_generated_files(html_code, css_code, js_code)
        
        update_progress("Processing complete", 100)
        processing_complete = True
        
    except Exception as e:
        error_message = str(e)
        update_progress(f"Error: {str(e)}", 0)
    finally:
        is_processing = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    global is_processing, processing_complete, error_message
    
    # Reset state
    is_processing = True
    processing_complete = False
    error_message = None
    update_progress("Starting process", 0)
    
    if 'file' not in request.files:
        is_processing = False
        return jsonify({'error': 'No file part'})
    
    file = request.files['file']
    
    if file.filename == '':
        is_processing = False
        return jsonify({'error': 'No selected file'})
    
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Start processing in a separate thread
        thread = threading.Thread(target=process_image, args=(file_path,))
        thread.start()
        
        return jsonify({'message': 'Processing started'})

@app.route('/progress')
def get_progress():
    return jsonify({
        'task': current_task,
        'percentage': progress_percentage,
        'isProcessing': is_processing,
        'complete': processing_complete,
        'error': error_message
    })

@app.route('/result')
def get_result():
    if processing_complete:
        return jsonify({
            'html_path': '/generated/index.html',
            'css_path': '/generated/styles.css',
            'js_path': '/generated/script.js'
        })
    else:
        return jsonify({'error': 'Processing not complete'})

@app.route('/generated/<path:filename>')
def generated_files(filename):
    return send_from_directory(app.config['GENERATED_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
