# UI to Code Generator

This project uses AWS Bedrock with Anthropic Claude 3.7 Sonnet to generate responsive web code from UI design images.

## Project Overview

This tool allows you to:
1. Upload a UI design image through a web interface
2. Process the image using AWS Bedrock's Claude 3.7 Sonnet model
3. Generate responsive HTML, CSS, and JavaScript code based on the image
4. Save the generated code to local files
5. Track the progress of code generation in real-time

## Project Structure

- `app.py` - Main Python application with Flask server and AWS Bedrock integration
- `templates/index.html` - Web interface for image upload and progress tracking
- `uploads/` - Directory for storing uploaded images
- `generated/` - Directory for storing generated code files
  - `index.html` - Generated HTML file
  - `styles.css` - Generated CSS file
  - `script.js` - Generated JavaScript file
- `requirements.txt` - Python dependencies

## Technologies Used

- **Python** - Backend implementation
- **Flask** - Web server framework
- **AWS Bedrock** - AI service for image processing and code generation
- **Anthropic Claude 3.7 Sonnet** - Large language model for code generation
- **Bootstrap 5** - Frontend UI components
- **Font Awesome** - Icons for the interface

## Setup and Installation

1. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```

2. Ensure you have AWS credentials configured with access to Bedrock in the us-east-1 region

3. Run the application:
   ```
   python app.py
   ```

4. Open your browser and navigate to `http://127.0.0.1:5000`

## How to Use

1. Upload a UI design image using the web interface
2. Click "Generate Code" to start the process
3. Monitor the progress in real-time
4. Once complete, view or download the generated HTML, CSS, and JavaScript files

## Notes

- The generated code uses Bootstrap 5 for responsive layout
- The tool is designed for frontend code generation only
- Maximum upload size is 16MB
- Supported image formats: JPG, PNG
