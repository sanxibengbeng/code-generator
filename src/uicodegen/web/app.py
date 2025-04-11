import os
import sys
from flask import Flask

# Add the project root directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from uicodegen.core.session_manager import SessionManager
from uicodegen.web.routes import init_app

def create_app(test_config=None):
    """Create and configure the Flask application"""
    # Get the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    
    app = Flask(__name__, 
                static_folder=os.path.join(project_root, 'generated'),
                template_folder=os.path.join(project_root, 'templates'))
    
    # Default configuration
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev_secret_key_change_in_production'),
        UPLOAD_FOLDER=os.path.join(project_root, 'uploads'),
        GENERATED_FOLDER=os.path.join(project_root, 'generated'),
        MAX_CONTENT_LENGTH=16 * 1024 * 1024  # 16MB max upload
    )
    
    # Override config with test config if provided
    if test_config:
        app.config.update(test_config)
    
    # Ensure directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['GENERATED_FOLDER'], exist_ok=True)
    
    # Initialize session manager
    session_manager = SessionManager(
        upload_base_dir=app.config['UPLOAD_FOLDER'],
        generated_base_dir=app.config['GENERATED_FOLDER']
    )
    
    # Initialize routes
    init_app(app, session_manager)
    
    return app
