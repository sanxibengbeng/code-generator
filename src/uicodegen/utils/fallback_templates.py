"""
Fallback templates for when code generation fails
"""

def create_fallback_html(partial_response=""):
    """Create fallback HTML when extraction fails"""
    return """
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
                    """ + partial_response + """
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

def create_fallback_css():
    """Create fallback CSS when extraction fails"""
    return """
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

def create_fallback_js():
    """Create fallback JavaScript when extraction fails"""
    return """
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

def create_timeout_html():
    """Create HTML for timeout errors"""
    return """
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

def create_error_html(error_message):
    """Create HTML for general errors"""
    return f"""
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
