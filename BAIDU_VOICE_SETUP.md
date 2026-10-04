# 百度语音本地连接

请先撤销聊天中暴露的凭证并生成新凭证，然后运行：

```sh
export BAIDU_API_KEY='你的新 API Key'
export BAIDU_SECRET_KEY='你的新 Secret Key'
export LLM_API_KEY='你的大模型 API Key'
export LLM_BASE_URL='https://api.deepseek.com'
export LLM_MODEL='deepseek-chat'
python3 /Users/hillary/Documents/Codex/2026-09-24/wo/baidu_voice_server.py
```

保持终端运行，然后打开 `http://127.0.0.1:8000/`。该地址会直接显示语音 App；健康检查地址为 `http://127.0.0.1:8000/api/health`。
