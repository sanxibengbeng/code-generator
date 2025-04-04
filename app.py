import os
import base64
import json
import time
import boto3
import threading
import botocore.config
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
selected_model = "claude-3-7-sonnet"  # Default model
use_streaming = False  # Default to non-streaming mode

# Metrics tracking
input_tokens = 0
output_tokens = 0
processing_time = 0
streaming_chunks = 0

# Model configurations
MODEL_CONFIGS = {
    "claude-3-5-sonnet": {
        "model_id": "anthropic.claude-3-5-sonnet-20240620-v1:0",
        "max_tokens": 8000
    },
    "claude-3-7-sonnet": {
        "model_id": "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        "max_tokens": 40960
    }
}

# Configure boto3 with increased timeouts
boto_config = botocore.config.Config(
    connect_timeout=120,    # 2 minutes
    read_timeout=600,       # 10 minutes
    retries={'max_attempts': 3, 'mode': 'standard'}
)

# Initialize Bedrock client with increased timeouts
bedrock_runtime = boto3.client(
    service_name='bedrock-runtime',
    region_name='us-east-1',
    config=boto_config
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

def extract_code_from_text(full_text, debug_file=None):
    """Extract HTML, CSS, and JS code from the model response text"""
    html_code = ""
    css_code = ""
    js_code = ""
    
    # Log extraction attempt if debug file is provided
    if debug_file:
        debug_file.write("\n=== CODE EXTRACTION ATTEMPT ===\n")
        debug_file.write(f"Full text length: {len(full_text)}\n")
    
    # Extract HTML
    html_start = full_text.find("```html")
    if debug_file:
        debug_file.write(f"HTML start position: {html_start}\n")
    
    if html_start != -1:
        html_end = full_text.find("```", html_start + 6)
        if debug_file:
            debug_file.write(f"HTML end position: {html_end}\n")
        
        if html_end != -1:
            html_code = full_text[html_start + 6:html_end].strip()
            if debug_file:
                debug_file.write(f"Extracted HTML length: {len(html_code)}\n")
                debug_file.write(f"HTML snippet: {html_code[:100]}...\n")
    
    # Extract CSS
    css_start = full_text.find("```css")
    if debug_file:
        debug_file.write(f"CSS start position: {css_start}\n")
    
    if css_start != -1:
        css_end = full_text.find("```", css_start + 6)
        if debug_file:
            debug_file.write(f"CSS end position: {css_end}\n")
        
        if css_end != -1:
            css_code = full_text[css_start + 6:css_end].strip()
            if debug_file:
                debug_file.write(f"Extracted CSS length: {len(css_code)}\n")
                debug_file.write(f"CSS snippet: {css_code[:100]}...\n")
    
    # Extract JS - try both javascript and js tags
    js_start = full_text.find("```javascript")
    if js_start == -1:
        js_start = full_text.find("```js")
        js_prefix_len = 5  # Length of "```js"
    else:
        js_prefix_len = 14  # Length of "```javascript"
    
    if debug_file:
        debug_file.write(f"JS start position: {js_start} (prefix length: {js_prefix_len})\n")
    
    if js_start != -1:
        js_end = full_text.find("```", js_start + js_prefix_len)
        if debug_file:
            debug_file.write(f"JS end position: {js_end}\n")
        
        if js_end != -1:
            js_code = full_text[js_start + js_prefix_len:js_end].strip()
            if debug_file:
                debug_file.write(f"Extracted JS length: {len(js_code)}\n")
                debug_file.write(f"JS snippet: {js_code[:100]}...\n")
    
    # Alternative extraction for malformed code blocks
    if (html_code == "" or css_code == "" or js_code == "") and debug_file:
        debug_file.write("\n=== ATTEMPTING ALTERNATIVE EXTRACTION ===\n")
        
        # Look for sections even without proper markdown code blocks
        sections = full_text.split("```")
        if len(sections) > 1:
            debug_file.write(f"Found {len(sections)} sections separated by ```\n")
            
            for i, section in enumerate(sections):
                section_preview = section[:50].replace('\n', ' ')
                debug_file.write(f"Section {i}: {section_preview}...\n")
                
                # Try to identify content by common patterns
                if html_code == "" and ("html" in section.lower()[:20] or "<html" in section.lower() or "<!doctype" in section.lower()):
                    html_code = section.strip()
                    if "html" in section.lower()[:20]:
                        html_code = html_code[section.lower().find("html") + 4:].strip()
                    debug_file.write(f"Found potential HTML in section {i}\n")
                
                elif css_code == "" and "css" in section.lower()[:20]:
                    css_code = section.strip()
                    css_code = css_code[section.lower().find("css") + 3:].strip()
                    debug_file.write(f"Found potential CSS in section {i}\n")
                
                elif js_code == "" and ("javascript" in section.lower()[:30] or "js" in section.lower()[:10]):
                    js_code = section.strip()
                    if "javascript" in section.lower()[:30]:
                        js_code = js_code[section.lower().find("javascript") + 10:].strip()
                    elif "js" in section.lower()[:10]:
                        js_code = js_code[section.lower().find("js") + 2:].strip()
                    debug_file.write(f"Found potential JS in section {i}\n")
    
    return html_code, css_code, js_code

def process_image_streaming(image_path):
    """Process the image with selected Bedrock Claude model using streaming API"""
    global is_processing, processing_complete, error_message, selected_model
    global input_tokens, output_tokens, processing_time, streaming_chunks
    
    try:
        start_time = time.time()
        update_progress("Preparing image for streaming processing", 10)
        
        # Encode image to base64
        base64_image = encode_image(image_path)
        
        update_progress("Connecting to AWS Bedrock for streaming", 15)
        
        # Get model configuration
        model_config = MODEL_CONFIGS[selected_model]
        model_id = model_config["model_id"]
        max_tokens = model_config["max_tokens"]
        model_display_name = selected_model.replace("-", " ").title()
        
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
        
        update_progress(f"Sending streaming request to {model_display_name}", 20)
        
        # Create the request payload
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
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
        
        update_progress(f"Starting streaming with {model_display_name}", 25)
        
        try:
            # Invoke the model with streaming
            response = bedrock_runtime.invoke_model_with_response_stream(
                modelId=model_id,
                body=request_body_json
            )
            
            # Process the streaming response
            stream = response.get('body')
            
            # Initialize variables for collecting response
            full_text = ""
            chunk_count = 0
            
            # Create a debug log file for chunks
            debug_log_path = os.path.join(app.config['GENERATED_FOLDER'], 'streaming_debug.log')
            with open(debug_log_path, 'w') as debug_file:
                debug_file.write("=== STREAMING DEBUG LOG ===\n\n")
                
                # Process each chunk
                for event in stream:
                    chunk = event.get('chunk')
                    if chunk:
                        chunk_data = json.loads(chunk.get('bytes').decode())
                        
                        # Log the raw chunk data
                        debug_file.write(f"--- CHUNK {chunk_count + 1} ---\n")
                        debug_file.write(f"Raw chunk data: {json.dumps(chunk_data, indent=2)}\n\n")
                        
                        # Extract text from the chunk
                        chunk_text = ""
                        
                        # Handle different types of chunks
                        if chunk_data.get('type') == 'content_block_delta':
                            delta = chunk_data.get('delta', {})
                            if delta.get('type') == 'text_delta':
                                chunk_text = delta.get('text', '')
                                full_text += chunk_text
                        elif chunk_data.get('type') == 'message_delta' and 'usage' in chunk_data:
                            # Extract token usage from message_delta
                            if 'output_tokens' in chunk_data.get('usage', {}):
                                output_tokens = chunk_data['usage']['output_tokens']
                        elif chunk_data.get('type') == 'message_stop' and 'amazon-bedrock-invocationMetrics' in chunk_data:
                            # Extract metrics from message_stop
                            metrics = chunk_data.get('amazon-bedrock-invocationMetrics', {})
                            input_tokens = metrics.get('inputTokenCount', 0)
                            output_tokens = metrics.get('outputTokenCount', 0)
                        
                        # Log the extracted text
                        debug_file.write(f"Extracted text: {chunk_text}\n")
                        debug_file.write(f"Current full_text length: {len(full_text)}\n")
                        debug_file.write("-------------------\n\n")
                        
                        # Update progress based on chunk count
                        chunk_count += 1
                        streaming_chunks = chunk_count
                        
                        # Dynamic progress update based on content received
                        # We'll estimate progress between 25-90% during streaming
                        if "```html" in full_text and progress_percentage < 40:
                            update_progress("Generating HTML code", 40)
                            debug_file.write("HTML marker found\n")
                        elif "```css" in full_text and progress_percentage < 60:
                            update_progress("Generating CSS code", 60)
                            debug_file.write("CSS marker found\n")
                        elif "```javascript" in full_text and progress_percentage < 80:
                            update_progress("Generating JavaScript code", 80)
                            debug_file.write("JavaScript marker found\n")
                        else:
                            # Gradual progress update
                            current_progress = min(25 + (chunk_count * 65 / 100), 90)
                            update_progress(f"Processing chunk {chunk_count}", int(current_progress))
                
                # Log the final full text
                debug_file.write("\n=== FINAL FULL TEXT ===\n")
                debug_file.write(full_text)
                debug_file.write("\n\n=== END OF LOG ===\n")
            
            update_progress("Extracting code from streaming response", 90)
            
            # Extract code from the full text with debug logging
            with open(os.path.join(app.config['GENERATED_FOLDER'], 'extraction_debug.log'), 'w') as extract_debug:
                html_code, css_code, js_code = extract_code_from_text(full_text, extract_debug)
                
                # If extraction failed, try to create minimal files
                if not html_code:
                    extract_debug.write("\n=== CREATING FALLBACK HTML ===\n")
                    html_code = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generated UI</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <!-- The model failed to generate proper HTML code -->
    <div class="container mt-5">
        <div class="alert alert-warning">
            <h4>Code Generation Issue</h4>
            <p>The AI model failed to generate proper HTML code from the image. Please check the streaming_debug.log file for details.</p>
        </div>
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Raw Response</h5>
                <pre class="bg-light p-3" style="max-height: 300px; overflow-y: auto;">
                    """ + full_text[:1000] + """
                    ...
                </pre>
            </div>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/vue@3.2.26/dist/vue.global.min.js"></script>
    <script src="script.js"></script>
</body>
</html>
                    """
                
                if not css_code:
                    extract_debug.write("\n=== CREATING FALLBACK CSS ===\n")
                    css_code = """
/* Fallback CSS - The model failed to generate proper CSS */
body {
    font-family: 'Arial', sans-serif;
    background-color: #f8f9fa;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
}
                    """
                
                if not js_code:
                    extract_debug.write("\n=== CREATING FALLBACK JS ===\n")
                    js_code = """
// Fallback JavaScript - The model failed to generate proper JS code
console.log('UI to Code Generator - Fallback JavaScript');

// Initialize Vue app
const app = Vue.createApp({
    data() {
        return {
            message: 'The AI model failed to generate proper JavaScript code.'
        }
    }
});

// Mount Vue app
app.mount('#app');
                    """
        
        except botocore.exceptions.ReadTimeoutError:
            error_message = "Read timeout occurred. The request took too long to complete. Try using a smaller image or the non-streaming mode."
            update_progress(error_message, 0)
            
            # Create fallback files in case of timeout
            html_code = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Timeout Error</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5">
        <div class="alert alert-danger">
            <h4>Request Timeout</h4>
            <p>The request to AWS Bedrock timed out. This can happen with large or complex images.</p>
            <hr>
            <p>Suggestions:</p>
            <ul>
                <li>Try using a smaller or simpler image</li>
                <li>Switch to the non-streaming mode</li>
                <li>Try the Claude 3.5 Sonnet model which may be faster</li>
            </ul>
        </div>
    </div>
</body>
</html>
            """
            
            css_code = "/* No CSS generated due to timeout */"
            js_code = "// No JavaScript generated due to timeout"
            
            # Save these fallback files
            file_paths = save_generated_files(html_code, css_code, js_code)
            processing_complete = True
            return
            
        update_progress("Saving generated files", 95)
        
        # Save the generated code to files
        file_paths = save_generated_files(html_code, css_code, js_code)
        
        # Calculate processing time
        processing_time = round(time.time() - start_time, 2)
        
        update_progress("Processing complete", 100)
        processing_complete = True
        
    except Exception as e:
        error_message = str(e)
        update_progress(f"Error in streaming: {str(e)}", 0)
        
        # Create fallback files in case of error
        html_code = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Error Occurred</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5">
        <div class="alert alert-danger">
            <h4>Error During Processing</h4>
            <p>An error occurred while processing your image:</p>
            <pre class="bg-light p-3">{error_message}</pre>
        </div>
    </div>
</body>
</html>
        """
        
        css_code = "/* No CSS generated due to error */"
        js_code = "// No JavaScript generated due to error"
        
        # Save these fallback files
        file_paths = save_generated_files(html_code, css_code, js_code)
        processing_complete = True
    finally:
        is_processing = False

def process_image_non_streaming(image_path):
    """Process the image with selected Bedrock Claude model using non-streaming API"""
    global is_processing, processing_complete, error_message, selected_model
    global input_tokens, output_tokens, processing_time
    
    try:
        start_time = time.time()
        update_progress("Preparing image for processing", 10)
        
        # Encode image to base64
        base64_image = encode_image(image_path)
        
        update_progress("Connecting to AWS Bedrock", 20)
        
        # Get model configuration
        model_config = MODEL_CONFIGS[selected_model]
        model_id = model_config["model_id"]
        max_tokens = model_config["max_tokens"]
        model_display_name = selected_model.replace("-", " ").title()
        
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
        
        update_progress(f"Sending request to {model_display_name}", 30)
        
        # Create the request payload
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
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
        
        update_progress(f"Processing with {model_display_name}", 40)
        
        # Invoke the model
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=request_body_json
        )
        
        update_progress("Parsing response", 70)
        
        # Parse the response
        response_body = json.loads(response.get('body').read())
        content = response_body.get('content', [])
        
        # Get usage metrics if available
        if 'usage' in response_body:
            input_tokens = response_body['usage'].get('input_tokens', 0)
            output_tokens = response_body['usage'].get('output_tokens', 0)
        
        # Extract text from the response
        full_text = ""
        for item in content:
            if item.get('type') == 'text':
                full_text += item.get('text', '')
        
        update_progress("Extracting code from response", 80)
        
        # Extract code from the full text
        html_code, css_code, js_code = extract_code_from_text(full_text)
        
        update_progress("Saving generated files", 90)
        
        # Save the generated code to files
        file_paths = save_generated_files(html_code, css_code, js_code)
        
        # Calculate processing time
        processing_time = round(time.time() - start_time, 2)
        
        update_progress("Processing complete", 100)
        processing_complete = True
        
    except Exception as e:
        error_message = str(e)
        update_progress(f"Error: {str(e)}", 0)
    finally:
        is_processing = False

def process_image(image_path):
    """Process the image with selected Bedrock Claude model"""
    global use_streaming
    
    if use_streaming:
        process_image_streaming(image_path)
    else:
        process_image_non_streaming(image_path)

@app.route('/')
def index():
    return render_template('index.html', models=list(MODEL_CONFIGS.keys()))

@app.route('/upload', methods=['POST'])
def upload_file():
    global is_processing, processing_complete, error_message, selected_model, use_streaming
    global input_tokens, output_tokens, processing_time, streaming_chunks
    
    # Reset state
    is_processing = True
    processing_complete = False
    error_message = None
    input_tokens = 0
    output_tokens = 0
    processing_time = 0
    streaming_chunks = 0
    update_progress("Starting process", 0)
    
    if 'file' not in request.files:
        is_processing = False
        return jsonify({'error': 'No file part'})
    
    file = request.files['file']
    
    # Get selected model
    if 'model' in request.form:
        model_name = request.form['model']
        if model_name in MODEL_CONFIGS:
            selected_model = model_name
    
    # Get streaming preference
    if 'streaming' in request.form:
        use_streaming = request.form['streaming'].lower() == 'true'
    
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
        
        return jsonify({
            'message': 'Processing started', 
            'model': selected_model,
            'streaming': use_streaming
        })

@app.route('/progress')
def get_progress():
    return jsonify({
        'task': current_task,
        'percentage': progress_percentage,
        'isProcessing': is_processing,
        'complete': processing_complete,
        'error': error_message,
        'model': selected_model,
        'streaming': use_streaming,
        'streamingChunks': streaming_chunks
    })

@app.route('/result')
def get_result():
    if processing_complete:
        return jsonify({
            'html_path': '/generated/index.html',
            'css_path': '/generated/styles.css',
            'js_path': '/generated/script.js',
            'metrics': {
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'processing_time': processing_time,
                'streaming_chunks': streaming_chunks if use_streaming else 0
            }
        })
    else:
        return jsonify({'error': 'Processing not complete'})

@app.route('/generated/<path:filename>')
def generated_files(filename):
    return send_from_directory(app.config['GENERATED_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
