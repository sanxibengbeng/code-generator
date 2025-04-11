import os
import json
import time
import base64
import re
import threading
import botocore.config
from flask import Flask, request, render_template, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from session_manager import SessionManager

app = Flask(__name__, static_folder='generated')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
app.config['GENERATED_FOLDER'] = 'generated'
app.secret_key = os.environ.get('SECRET_KEY', 'dev_secret_key_change_in_production')

# Initialize session manager
session_manager = SessionManager(
    upload_base_dir=app.config['UPLOAD_FOLDER'],
    generated_base_dir=app.config['GENERATED_FOLDER']
)

# Default model
DEFAULT_MODEL = "claude-3-7-sonnet"

# Model configurations
MODEL_CONFIGS = {
    "claude-3-5-sonnet": {
        "model_id": "anthropic.claude-3-5-sonnet-20240620-v1:0",
        "max_tokens": 8000
    },
    "claude-3-7-sonnet": {
        "model_id": "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        "max_tokens": 40960
    },
    "claude-3-haiku": {
        "model_id": "anthropic.claude-3-haiku-20240307-v1:0",
        "max_tokens": 4096
    }
}

# Initialize AWS Bedrock client
try:
    import boto3
    from botocore.config import Config
    
    # Configure the AWS SDK
    config = Config(
        retries={
            'max_attempts': 10,
            'mode': 'standard'
        }
    )
    
    # Create a Bedrock Runtime client
    bedrock_runtime = boto3.client(
        service_name='bedrock-runtime',
        config=config
    )
except Exception as e:
    print(f"Error initializing AWS Bedrock client: {str(e)}")
    bedrock_runtime = None

def encode_image(image_path):
    """Encode image to base64"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def save_generated_files(session_id, html_content, css_content, js_content):
    """Save the generated code to files in the session directory"""
    file_paths = {}
    
    # Save HTML
    html_path = session_manager.get_generated_path(session_id, 'index.html')
    with open(html_path, 'w') as f:
        f.write(html_content)
    file_paths['html'] = html_path
    
    # Save CSS
    css_path = session_manager.get_generated_path(session_id, 'styles.css')
    with open(css_path, 'w') as f:
        f.write(css_content)
    file_paths['css'] = css_path
    
    # Save JS
    js_path = session_manager.get_generated_path(session_id, 'script.js')
    with open(js_path, 'w') as f:
        f.write(js_content)
    file_paths['js'] = js_path
    
    return file_paths

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

def process_image_streaming(session_id, image_path):
    """Process the image with selected Bedrock Claude model using streaming API"""
    # Get session status
    status = session_manager.get_session_status(session_id)
    selected_model = status.get('selected_model', DEFAULT_MODEL)
    
    try:
        start_time = time.time()
        session_manager.update_session_status(
            session_id,
            current_task="Preparing image for streaming processing",
            progress_percentage=10,
            is_processing=True,
            processing_complete=False,
            error_message=None
        )
        
        # Encode image to base64
        base64_image = encode_image(image_path)
        
        session_manager.update_session_status(
            session_id,
            current_task="Connecting to AWS Bedrock for streaming",
            progress_percentage=15
        )
        
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
        
        session_manager.update_session_status(
            session_id,
            current_task=f"Sending streaming request to {model_display_name}",
            progress_percentage=20
        )
        
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
        
        session_manager.update_session_status(
            session_id,
            current_task=f"Starting streaming with {model_display_name}",
            progress_percentage=25
        )
        
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
            debug_log_path = session_manager.get_generated_path(session_id, 'streaming_debug.log')
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
                                session_manager.update_session_status(
                                    session_id,
                                    output_tokens=output_tokens
                                )
                        elif chunk_data.get('type') == 'message_stop' and 'amazon-bedrock-invocationMetrics' in chunk_data:
                            # Extract metrics from message_stop
                            metrics = chunk_data.get('amazon-bedrock-invocationMetrics', {})
                            input_tokens = metrics.get('inputTokenCount', 0)
                            output_tokens = metrics.get('outputTokenCount', 0)
                            session_manager.update_session_status(
                                session_id,
                                input_tokens=input_tokens,
                                output_tokens=output_tokens
                            )
                        
                        # Log the extracted text
                        debug_file.write(f"Extracted text: {chunk_text}\n")
                        debug_file.write(f"Current full_text length: {len(full_text)}\n")
                        debug_file.write("-------------------\n\n")
                        
                        # Update progress based on chunk count
                        chunk_count += 1
                        session_manager.update_session_status(
                            session_id,
                            streaming_chunks=chunk_count
                        )
                        
                        # Dynamic progress update based on content received
                        # We'll estimate progress between 25-90% during streaming
                        current_status = session_manager.get_session_status(session_id)
                        current_progress = current_status['progress_percentage']
                        
                        if "```html" in full_text and current_progress < 40:
                            session_manager.update_session_status(
                                session_id,
                                current_task="Generating HTML code",
                                progress_percentage=40
                            )
                            debug_file.write("HTML marker found\n")
                        elif "```css" in full_text and current_progress < 60:
                            session_manager.update_session_status(
                                session_id,
                                current_task="Generating CSS code",
                                progress_percentage=60
                            )
                            debug_file.write("CSS marker found\n")
                        elif "```javascript" in full_text and current_progress < 80:
                            session_manager.update_session_status(
                                session_id,
                                current_task="Generating JavaScript code",
                                progress_percentage=80
                            )
                            debug_file.write("JavaScript marker found\n")
                        else:
                            # Gradual progress update
                            current_progress = min(25 + (chunk_count * 65 / 100), 90)
                            session_manager.update_session_status(
                                session_id,
                                current_task=f"Processing chunk {chunk_count}",
                                progress_percentage=int(current_progress)
                            )
                
                # Log the final full text
                debug_file.write("\n=== FINAL FULL TEXT ===\n")
                debug_file.write(full_text)
                debug_file.write("\n\n=== END OF LOG ===\n")
            
            session_manager.update_session_status(
                session_id,
                current_task="Extracting code from streaming response",
                progress_percentage=90
            )
            
            # Extract code from the full text with debug logging
            extract_debug_path = session_manager.get_generated_path(session_id, 'extraction_debug.log')
            with open(extract_debug_path, 'w') as extract_debug:
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
            session_manager.update_session_status(
                session_id,
                current_task=error_message,
                progress_percentage=0,
                error_message=error_message
            )
            
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
            file_paths = save_generated_files(session_id, html_code, css_code, js_code)
            session_manager.update_session_status(
                session_id,
                processing_complete=True
            )
            return
            
        session_manager.update_session_status(
            session_id,
            current_task="Saving generated files",
            progress_percentage=95
        )
        
        # Save the generated code to files
        file_paths = save_generated_files(session_id, html_code, css_code, js_code)
        
        # Calculate processing time
        processing_time = round(time.time() - start_time, 2)
        
        session_manager.update_session_status(
            session_id,
            current_task="Processing complete",
            progress_percentage=100,
            processing_complete=True,
            processing_time=processing_time
        )
        
    except Exception as e:
        error_message = str(e)
        session_manager.update_session_status(
            session_id,
            current_task=f"Error in streaming: {str(e)}",
            progress_percentage=0,
            error_message=error_message
        )
        
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
        file_paths = save_generated_files(session_id, html_code, css_code, js_code)
        session_manager.update_session_status(
            session_id,
            processing_complete=True
        )
    finally:
        session_manager.update_session_status(
            session_id,
            is_processing=False
        )
def process_image_non_streaming(session_id, image_path):
    """Process the image with selected Bedrock Claude model using non-streaming API"""
    # Get session status
    status = session_manager.get_session_status(session_id)
    selected_model = status.get('selected_model', DEFAULT_MODEL)
    
    try:
        start_time = time.time()
        session_manager.update_session_status(
            session_id,
            current_task="Preparing image for processing",
            progress_percentage=10,
            is_processing=True,
            processing_complete=False,
            error_message=None
        )
        
        # Encode image to base64
        base64_image = encode_image(image_path)
        
        session_manager.update_session_status(
            session_id,
            current_task="Connecting to AWS Bedrock",
            progress_percentage=20
        )
        
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
        
        session_manager.update_session_status(
            session_id,
            current_task=f"Sending request to {model_display_name}",
            progress_percentage=30
        )
        
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
        
        session_manager.update_session_status(
            session_id,
            current_task=f"Processing with {model_display_name}",
            progress_percentage=40
        )
        
        # Invoke the model
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=request_body_json
        )
        
        session_manager.update_session_status(
            session_id,
            current_task="Parsing response",
            progress_percentage=70
        )
        
        # Parse the response
        response_body = json.loads(response.get('body').read())
        content = response_body.get('content', [])
        
        # Get usage metrics if available
        if 'usage' in response_body:
            input_tokens = response_body['usage'].get('input_tokens', 0)
            output_tokens = response_body['usage'].get('output_tokens', 0)
            session_manager.update_session_status(
                session_id,
                input_tokens=input_tokens,
                output_tokens=output_tokens
            )
        
        # Extract text from the response
        full_text = ""
        for item in content:
            if item.get('type') == 'text':
                full_text += item.get('text', '')
        
        session_manager.update_session_status(
            session_id,
            current_task="Extracting code from response",
            progress_percentage=80
        )
        
        # Extract code from the full text
        extract_debug_path = session_manager.get_generated_path(session_id, 'extraction_debug.log')
        with open(extract_debug_path, 'w') as extract_debug:
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
            <p>The AI model failed to generate proper HTML code from the image.</p>
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
        
        session_manager.update_session_status(
            session_id,
            current_task="Saving generated files",
            progress_percentage=90
        )
        
        # Save the generated code to files
        file_paths = save_generated_files(session_id, html_code, css_code, js_code)
        
        # Calculate processing time
        processing_time = round(time.time() - start_time, 2)
        
        session_manager.update_session_status(
            session_id,
            current_task="Processing complete",
            progress_percentage=100,
            processing_complete=True,
            processing_time=processing_time
        )
        
    except Exception as e:
        error_message = str(e)
        session_manager.update_session_status(
            session_id,
            current_task=f"Error: {str(e)}",
            progress_percentage=0,
            error_message=error_message
        )
    finally:
        session_manager.update_session_status(
            session_id,
            is_processing=False
        )

def process_image(session_id, image_path):
    """Process the image with selected Bedrock Claude model"""
    # Get session status
    status = session_manager.get_session_status(session_id)
    use_streaming = status['use_streaming']
    
    if use_streaming:
        process_image_streaming(session_id, image_path)
    else:
        process_image_non_streaming(session_id, image_path)
@app.route('/')
def index():
    return render_template('index.html', models=list(MODEL_CONFIGS.keys()))

@app.route('/upload', methods=['POST'])
def upload_file():
    # Create a new session
    session_id = session_manager.create_session()
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    
    file = request.files['file']
    
    # Get selected model
    selected_model = DEFAULT_MODEL
    if 'model' in request.form:
        model_name = request.form['model']
        if model_name in MODEL_CONFIGS:
            selected_model = model_name
    
    # Get streaming preference
    use_streaming = False
    if 'streaming' in request.form:
        use_streaming = request.form['streaming'].lower() == 'true'
    
    # Update session with selected options
    session_manager.update_session_status(
        session_id,
        selected_model=selected_model,
        use_streaming=use_streaming,
        current_task="Starting process",
        progress_percentage=0,
        is_processing=True,
        processing_complete=False,
        error_message=None,
        input_tokens=0,
        output_tokens=0,
        processing_time=0,
        streaming_chunks=0
    )
    
    if file.filename == '':
        session_manager.update_session_status(
            session_id,
            is_processing=False,
            error_message='No selected file'
        )
        return jsonify({'error': 'No selected file'})
    
    if file:
        filename = secure_filename(file.filename)
        file_path = session_manager.get_upload_path(session_id, filename)
        file.save(file_path)
        
        # Start processing in a separate thread
        thread = threading.Thread(target=process_image, args=(session_id, file_path))
        thread.start()
        
        return jsonify({
            'message': 'Processing started', 
            'session_id': session_id,
            'model': selected_model,
            'streaming': use_streaming
        })

@app.route('/progress/<session_id>')
def get_progress(session_id):
    status = session_manager.get_session_status(session_id)
    if status:
        return jsonify(status)
    else:
        return jsonify({'error': 'Session not found'}), 404

@app.route('/result/<session_id>')
def get_result(session_id):
    status = session_manager.get_session_status(session_id)
    
    if not status:
        return jsonify({'error': 'Session not found'}), 404
        
    if status['processing_complete']:
        return jsonify({
            'html_path': f'/generated/{session_id}/index.html',
            'css_path': f'/generated/{session_id}/styles.css',
            'js_path': f'/generated/{session_id}/script.js',
            'metrics': {
                'input_tokens': status['input_tokens'],
                'output_tokens': status['output_tokens'],
                'processing_time': status['processing_time'],
                'streaming_chunks': status['streaming_chunks'] if status['use_streaming'] else 0
            }
        })
    else:
        return jsonify({'error': 'Processing not complete'})

@app.route('/generated/<path:filename>')
def generated_files(filename):
    return send_from_directory(app.config['GENERATED_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
