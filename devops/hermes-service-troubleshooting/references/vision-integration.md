# 辅助 Vision 模型集成 — Qwen-VL-Max（阿里云百炼 DashScope）

## 场景
DeepSeek 等主模型不支持原生 vision。图片识别默认且只默认走 Qwen/DashScope；不要自动降级到 Tesseract OCR。配置 `auxiliary.vision` 让截图自动路由到通义千问。

## 完整配置步骤

### 1. 获取 API Key
去 [dashscope.aliyun.com](https://dashscope.aliyun.com) 申请，开通 Qwen-VL-Max。

### 2. 写入 config.yaml
```yaml
auxiliary:
  vision:
    provider: alibaba
    model: qwen-vl-max-latest
    base_url: ''
    api_key: ''
    timeout: 60
```

### 3. 跨 profile 同步
所有 profile（her-m2, default, english-tutor, finance）统一配置：
```python
import yaml
for prof in ['default', 'english-tutor', 'finance', 'her-m2']:
    path = f'/Users/mac/.hermes/profiles/{prof}/config.yaml'
    if prof == 'default':
        path = '/Users/mac/.hermes/config.yaml'
    with open(path) as f:
        cfg = yaml.safe_load(f)
    cfg['auxiliary']['vision']['provider'] = 'alibaba'
    cfg['auxiliary']['vision']['model'] = 'qwen-vl-max-latest'
    cfg['auxiliary']['vision']['base_url'] = ''
    cfg['auxiliary']['vision']['api_key'] = ''
    with open(path, 'w') as f:
        yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
```

### 4. 重启 gateway（必须！）
**配置写入后 gateway 不会自动热加载。** 必须重启：
```bash
# 除当前对话 gateway 以外全部重启
launchctl kickstart -k gui/501/ai.hermes.gateway           # default
launchctl kickstart -k gui/501/ai.hermes.gateway-english-tutor
launchctl kickstart -k gui/501/ai.hermes.gateway-finance

# her-m2 自己不能重启自己 — 用另一个 profile 的 cron 远程执行
cronjob create profile=default schedule="now+10s" \
  prompt="terminal: launchctl kickstart -k gui/501/ai.hermes.gateway-her-m2"
```

### 5. 验证
```bash
grep -A6 'vision:' /Users/mac/.hermes/profiles/her-m2/config.yaml | head -7
# provider: alibaba, model: qwen-vl-max-latest ✓
```

然后发截图测试 vision_analyze 是否返回精确的文字识别（不是泛泛描述）。

## 测试方法
用 curl 裸调 DashScope API 验证 key 有效性和识别精度：
```bash
curl -s https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $KEY" \
  -d '{"model":"qwen-vl-max-latest","messages":[{"role":"user","content":"回复1+1"}]}'
```

## 坑
- **config 改动不热加载**：gateway 必须在配置写入后重启才生效
- **her-m2 不能自杀**：交叉重启铁律 — 用另一个 gateway 的 cron 执行 kickstart
- **通义千问 vs Tesseract OCR**：前者识别精度远高于后者，尤其对中文财务截图（花呗、度小满等）
- **禁止自动降级**：Qwen/DashScope 没 key、没余额或 API 报错时，直接告诉波总配置/充值；不要改跑 Tesseract
