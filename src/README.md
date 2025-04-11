# UI Code Generator

A tool that converts UI design images into responsive HTML, CSS, and JavaScript code using AWS Bedrock and Claude AI models.

## Project Structure

```
src/
├── app.py                  # Original Flask application
├── app_new.py              # New entry point using refactored code
├── run_tests.py            # Script to run all tests
├── templates/              # HTML templates
├── uploads/                # Directory for uploaded images
├── generated/              # Directory for generated code
└── uicodegen/              # Main package
    ├── __init__.py
    ├── core/               # Core functionality
    │   ├── __init__.py
    │   ├── model_configs.py  # AI model configurations
    │   ├── processor.py      # Image processing logic
    │   └── session_manager.py # Session management
    ├── utils/              # Utility functions
    │   ├── __init__.py
    │   ├── code_extractor.py # Code extraction from AI responses
    │   ├── fallback_templates.py # Templates for error cases
    │   └── image_utils.py    # Image handling utilities
    ├── web/                # Web interface
    │   ├── __init__.py
    │   ├── app.py          # Flask app factory
    │   └── routes.py       # Flask routes
    └── tests/              # Unit tests
        ├── __init__.py
        ├── test_app_routes.py
        ├── test_code_extractor.py
        └── test_session_manager.py
```

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Configure AWS credentials:
   ```
   aws configure
   ```

3. Run the application:
   ```
   python app_new.py
   ```

## Running Tests

```
python run_tests.py
```

## Features

- Upload UI design images
- Convert designs to responsive HTML, CSS, and JavaScript code
- Support for multiple Claude AI models
- Streaming and non-streaming processing options
- Session-based processing with unique IDs
- Progress tracking and error handling
