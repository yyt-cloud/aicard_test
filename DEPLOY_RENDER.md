# Render 部署

本目录已包含 `Dockerfile` 与 `render.yaml`。Docker 镜像会安装 FFmpeg，将 Android WebView 常见的 WebM/Opus 录音转换为百度要求的 16 kHz 单声道 PCM。

部署时在 Render 创建 Blueprint/Web Service，并配置以下 Secret 环境变量：

- `BAIDU_API_KEY`
- `BAIDU_SECRET_KEY`
- `LLM_API_KEY`

不要把真实密钥提交到代码仓库。部署成功后，用 Render 提供的 HTTPS URL 替换 HTML 中的 `http://127.0.0.1:8000`。
