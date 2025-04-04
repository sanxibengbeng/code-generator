# UI 到代码生成器

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python 版本">
  <img src="https://img.shields.io/badge/AWS-Bedrock-orange.svg" alt="AWS Bedrock">
  <img src="https://img.shields.io/badge/Claude-3.7%20Sonnet-purple.svg" alt="Claude 3.7 Sonnet">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="许可证">
</p>

使用 AWS Bedrock 与 Anthropic Claude 3.7 Sonnet 将 UI 设计图片转换为响应式网页代码。

<p align="center">
  <a href="README.md">English Documentation</a>
</p>

## 🚀 功能特点

- 通过用户友好的网页界面上传 UI 设计图片
- 使用 AWS Bedrock 的 Claude 3.7 Sonnet 模型处理图片
- 基于图片生成响应式 HTML、CSS 和 JavaScript 代码
- 自动将生成的代码保存到本地文件
- 实时跟踪代码生成进度
- 支持流式和非流式 API 模式
- 显示处理指标（令牌数、时间、数据块）

## 📋 系统要求

- Python 3.8+
- 具有 Bedrock 访问权限的 AWS 账户
- 本地配置的 AWS 凭证

## 🛠️ 安装步骤

1. 克隆仓库：
   ```bash
   git clone https://github.com/yourusername/ui-to-code-generator.git
   cd ui-to-code-generator
   ```

2. 安装所需的 Python 包：
   ```bash
   pip install -r requirements.txt
   ```

3. 确保您已配置具有 us-east-1 区域 Bedrock 访问权限的 AWS 凭证。

## 🔧 项目结构

```
ui-to-code-generator/
├── app.py                 # 主 Python 应用程序与 Flask 服务器
├── templates/             # HTML 模板
│   └── index.html         # 图片上传的 Web 界面
├── uploads/               # 存储上传图片的目录
├── generated/             # 存储生成代码文件的目录
│   ├── index.html         # 生成的 HTML 文件
│   ├── styles.css         # 生成的 CSS 文件
│   └── script.js          # 生成的 JavaScript 文件
└── requirements.txt       # Python 依赖项
```

## 🚀 使用方法

1. 运行应用程序：
   ```bash
   python app.py
   ```

2. 在浏览器中访问 `http://127.0.0.1:8080`

3. 使用 Web 界面上传 UI 设计图片

4. 选择您偏好的模型和处理模式（流式或非流式）

5. 点击"生成代码"开始处理

6. 实时监控进度

7. 完成后，查看或下载生成的 HTML、CSS 和 JavaScript 文件

8. 查看处理指标（令牌数、时间等）

## 🔍 技术细节

- **后端**：Python 与 Flask Web 框架
- **AI 服务**：AWS Bedrock 与 Anthropic Claude 3.7 Sonnet
- **前端**：HTML、CSS、JavaScript 与 Bootstrap 5
- **图标**：Font Awesome
- **API 模式**：
  - 流式：具有动态进度的实时更新
  - 非流式：单一请求/响应模式

## 📝 注意事项

- 生成的代码使用 Bootstrap 5 实现响应式布局
- 该工具仅用于前端代码生成
- 最大上传大小为 16MB
- 支持的图片格式：JPG、PNG
- 应用程序使用线程处理以防止阻塞
- 通过轮询机制提供进度更新
- 流式模式提供更细粒度的进度更新，但对某些模型可能较慢

## 🤝 贡献

欢迎贡献、问题和功能请求！请随时查看[问题页面](https://github.com/yourusername/ui-to-code-generator/issues)。

## 📄 许可证

本项目采用 [MIT](LICENSE) 许可证。
