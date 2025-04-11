import os
import threading
from flask import Flask, request, render_template, jsonify, send_from_directory
from werkzeug.utils import secure_filename

from uicodegen.core.session_manager import SessionManager
from uicodegen.core.processor import process_image
from uicodegen.core.model_configs import MODEL_CONFIGS, DEFAULT_MODEL

def init_app(app, session_manager):
    """Initialize Flask routes"""
    
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
            thread = threading.Thread(target=process_image, args=(session_manager, session_id, file_path))
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
        print(f"Serving file: {app.config['GENERATED_FOLDER']}/{filename}")
        return send_from_directory(app.config['GENERATED_FOLDER'], filename, as_attachment=False)
