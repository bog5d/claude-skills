# 硅基流动 Vision 配置参考

## 配置方式

不能用 `patch` 或 `write_file` 直接改 config.yaml（工具拒绝安全敏感文件）。
必须用 `hermes config set` 命令：

```bash
cd ~/.hermes/profiles/finance
hermes config set auxiliary.vision.provider openai
hermes config set auxiliary.vision.model "Qwen/Qwen3-VL-32B-Instruct"
hermes config set auxiliary.vision.base_url "https://api.siliconflow.cn/v1"
hermes config set auxiliary.vision.api_key "sk-xxx..."
hermes config set auxiliary.vision.timeout 120
```

## 验证方法

### 1. 文本请求（确认 API 连通性）
```bash
curl -s https://api.siliconflow.cn/v1/chat/completions \
  -H "Authorization: Bearer sk-xxx..." \
  -H "Content-Type: application/json" \
  -d '{"model":"Qwen/Qwen3-VL-32B-Instruct","messages":[{"role":"user","content":"hi"}],"max_tokens":5}'
# 预期: 200 OK
```

### 2. 带图片请求（确认 Vision 能力）
```python
import requests, base64
api_key = "sk-xxx..."
with open('image.jpg', 'rb') as f:
    img_b64 = base64.b64encode(f.read()).decode()
resp = requests.post(
    'https://api.siliconflow.cn/v1/chat/completions',
    headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
    json={
        'model': 'Qwen/Qwen3-VL-32B-Instruct',
        'messages': [{'role': 'user', 'content': [
            {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{img_b64}'}},
            {'type': 'text', 'text': '读出截图所有文字'}
        ]}],
        'max_tokens': 500
    },
    timeout=30
)
print(resp.json()['choices'][0]['message']['content'])
```

## 已知问题

### "Model does not exist" (code 20012)
- 直接 API 文本请求 200 OK，但 `vision_analyze` 工具返回 400
- 原因：Hermes 在构造请求时模型名格式可能不同
- **解法**：确认 SiliconFlow 上该模型 ID 是否完全匹配，尝试换用 `Qwen/Qwen3-VL-8B-Instruct` 或 `Qwen/Qwen3-VL-32B-Instruct` 等可用模型
- 可用模型列表查询：`curl -s https://api.siliconflow.cn/v1/models -H "Authorization: Bearer sk-xxx..." | python3 -m json.tool | grep -i vl`

### 千问 Dashscope 欠费
- 原 Dashscope API (qwen-vl-max) 欠费时 `vision_analyze` 返回 `Arrearage` 错误
- 降级链路：SiliconFlow → Apple Vision → Tesseract

## 可用 VL 模型 (2026-07-04)
- Qwen/Qwen3-VL-32B-Instruct
- Qwen/Qwen3-VL-32B-Thinking
- Qwen/Qwen3-VL-8B-Instruct
- Qwen/Qwen3-VL-8B-Thinking
- Qwen/Qwen3-VL-30B-A3B-Instruct
- Qwen/Qwen3-VL-30B-A3B-Thinking

推荐：32B 版本效果最佳（截图 OCR），8B 版本更快但精度稍低。
