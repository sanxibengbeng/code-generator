# UI to Code Generator

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/AWS-Bedrock-orange.svg" alt="AWS Bedrock">
  <img src="https://img.shields.io/badge/Claude-3.7%20Sonnet-purple.svg" alt="Claude 3.7 Sonnet">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
</p>

Transform UI design images into responsive web code using AWS Bedrock with Anthropic Claude 3.7 Sonnet.

<p align="center">
  <a href="README_zh.md">中文文档</a>
</p>

## 🚀 Features

- Upload UI design images through a user-friendly web interface
- Process images using AWS Bedrock's Claude 3.7 Sonnet model
- Generate responsive HTML, CSS, and JavaScript code based on the image
- Save generated code to local files automatically
- Track code generation progress in real-time
- Support for both streaming and non-streaming API modes
- Display processing metrics (tokens, time, chunks)

## 📋 Requirements

- Python 3.8+
- AWS account with Bedrock access
- AWS credentials configured locally

## 🛠️ Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/sanxibengbeng/code-generator.git
   cd code-generator
   ```

2. Set up the Python virtual environment and install dependencies:
   ```bash
   cd src
   make env
   ```
   This command creates a virtual environment, upgrades pip, and installs all required packages.

3. Configure AWS credentials with access to Bedrock in the us-east-1 region:
   ```bash
   aws configure
   ```
   You'll need to provide:
   - AWS Access Key ID
   - AWS Secret Access Key
   - Default region name (use `us-east-1` for Bedrock)
   - Default output format (json recommended)

   Make sure your AWS account has access to the Bedrock service and the Claude models.

## 🔧 Project Structure

```
ui-to-code-generator/
├── src/                   # Source code directory
│   ├── app.py             # Main Python application with Flask server
│   ├── templates/         # HTML templates
│   │   └── index.html     # Web interface for image upload
│   ├── uploads/           # Directory for storing uploaded images
│   ├── generated/         # Directory for storing generated code files
│   │   ├── index.html     # Generated HTML file
│   │   ├── styles.css     # Generated CSS file
│   │   └── script.js      # Generated JavaScript file
│   ├── Makefile           # Make commands for project management
│   └── requirements.txt   # Python dependencies
├── cdk/                   # AWS CDK deployment code
└── web-design.png         # Sample design image
```

## 🚀 Usage

### Local Development

1. Run the application:
   ```bash
   cd src
   make run
   ```

2. Open your browser and navigate to `http://127.0.0.1:8080`

3. Upload a UI design image using the web interface

4. Select your preferred model and processing mode (streaming or non-streaming)

5. Click "Generate Code" to start the process

6. Monitor the progress in real-time

7. Once complete, view or download the generated HTML, CSS, and JavaScript files

8. Review processing metrics (tokens, time, etc.)

### AWS Deployment

1. Navigate to the CDK directory:
   ```bash
   cd cdk
   ```

2. Install CDK dependencies:
   ```bash
   npm install
   ```

3. Deploy to AWS:
   ```bash
   ./deploy.sh
   ```

4. After deployment, access the application using the LoadBalancer DNS provided in the outputs.

5. Log in with the default admin credentials:
   - Username: `admin`
   - Password: `admin@codegen`

## 🔍 Technical Details

- **Backend**: Python with Flask web framework
- **AI Service**: AWS Bedrock with Anthropic Claude 3.7 Sonnet
- **Frontend**: HTML, CSS, JavaScript with Bootstrap 5
- **Icons**: Font Awesome
- **API Modes**: 
  - Streaming: Real-time updates with dynamic progress
  - Non-streaming: Single request/response pattern
- **AWS Deployment**:
  - EC2 instances in Auto Scaling Group
  - Application Load Balancer
  - Cognito authentication
  - CDK for infrastructure as code

## 📝 Notes

- The generated code uses Bootstrap 5 for responsive layout
- The tool is designed for frontend code generation only
- Maximum upload size is 16MB
- Supported image formats: JPG, PNG
- The application uses threading to prevent blocking during processing
- Progress updates are provided through a polling mechanism
- Streaming mode provides more granular progress updates but may be slower for some models

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/sanxibengbeng/code-generator/issues).

## 📄 License

This project is [MIT](LICENSE) licensed.
