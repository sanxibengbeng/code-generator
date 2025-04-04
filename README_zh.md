# UI代码生成器

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python版本">
  <img src="https://img.shields.io/badge/AWS-Bedrock-orange.svg" alt="AWS Bedrock">
  <img src="https://img.shields.io/badge/Claude-3.7%20Sonnet-purple.svg" alt="Claude 3.7 Sonnet">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="许可证">
</p>

使用AWS Bedrock与Anthropic Claude 3.7 Sonnet将UI设计图片转换为响应式网页代码。

<p align="center">
  <a href="README.md">English Documentation</a>
</p>

## 🚀 功能特点

- 通过用户友好的Web界面上传UI设计图片
- 使用AWS Bedrock的Claude 3.7 Sonnet模型处理图片
- 基于图片生成响应式HTML、CSS和JavaScript代码
- 自动将生成的代码保存到本地文件
- 实时跟踪代码生成进度
- 支持流式和非流式API模式
- 显示处理指标（令牌数、时间、数据块）

## 📋 系统要求

- Python 3.8+
- 具有Bedrock访问权限的AWS账户
- 本地配置的AWS凭证

## 🛠️ 安装

1. 克隆仓库：
   ```bash
   git clone https://github.com/sanxibengbeng/code-generator.git
   cd code-generator
   ```

2. 设置Python虚拟环境并安装依赖：
   ```bash
   make env
   ```
   此命令会创建虚拟环境，升级pip，并安装所有必需的软件包。

3. 配置AWS凭证，确保有Bedrock服务的访问权限（us-east-1区域）：
   ```bash
   aws configure
   ```
   您需要提供：
   - AWS访问密钥ID
   - AWS秘密访问密钥
   - 默认区域名称（使用`us-east-1`以访问Bedrock）
   - 默认输出格式（推荐使用json）

   确保您的AWS账户有权访问Bedrock服务和Claude模型。

## 🔧 项目结构

```
ui-to-code-generator/
├── app.py                 # 主Python应用程序与Flask服务器
├── templates/             # HTML模板
│   └── index.html         # 图片上传的Web界面
├── uploads/               # 存储上传图片的目录
├── generated/             # 存储生成代码文件的目录
│   ├── index.html         # 生成的HTML文件
│   ├── styles.css         # 生成的CSS文件
│   └── script.js          # 生成的JavaScript文件
└── requirements.txt       # Python依赖项
```

## 🚀 使用方法

1. 运行应用程序：
   ```bash
   make run
   ```

2. 在浏览器中访问 `http://127.0.0.1:8080`

3. 使用Web界面上传UI设计图片

4. 选择您偏好的模型和处理模式（流式或非流式）

5. 点击"生成代码"开始处理

6. 实时监控进度

7. 完成后，查看或下载生成的HTML、CSS和JavaScript文件

8. 查看处理指标（令牌数、时间等）

## 🔍 技术细节

- **后端**：使用Flask Web框架的Python
- **AI服务**：使用Anthropic Claude 3.7 Sonnet的AWS Bedrock
- **前端**：使用Bootstrap 5的HTML、CSS、JavaScript
- **图标**：Font Awesome
- **API模式**：
  - 流式：具有动态进度的实时更新
  - 非流式：单一请求/响应模式

## 📝 注意事项

- 生成的代码使用Bootstrap 5实现响应式布局
- 该工具仅用于前端代码生成
- 最大上传大小为16MB
- 支持的图片格式：JPG、PNG
- 应用程序使用线程处理以防止处理过程中阻塞
- 通过轮询机制提供进度更新
- 流式模式提供更细粒度的进度更新，但对某些模型可能较慢

## 🤝 贡献

欢迎贡献、问题和功能请求！请随时查看[问题页面](https://github.com/sanxibengbeng/code-generator/issues)。

## 📄 许可证

本项目采用[MIT](LICENSE)许可证。
