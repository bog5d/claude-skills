# 硅基流动 Vision API 直调模板（已验证 2026-07-22）

## 场景
当 `vision_analyze` 工具不可用、env 变量从 terminal() 穿透不过去时，
用此模板直接在 terminal 中调用硅基流动 API 识别截图。

## 前提
- 知道 SILICONFLOW_API_KEY（从 env / .env / 波总处获取）
- API endpoint: `https://api.siliconflow.cn/v1/chat/completions`
- Model: `Qwen/Qwen3-VL-32B-Instruct`

## 模板

```python
import json, base64, urllib.request

API_KEY = 'sk-xxx...'  # ← 替换为实际 key

def encode_image(path):
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode()

paths = [
    '/Users/mac/.hermes/profiles/finance/image_cache/img_file1.jpg',
    '/Users/mac/.hermes/profiles/finance/image_cache/img_file2.jpg',
]

for i, path in enumerate(paths):
    img = encode_image(path)
    prompt = '你是OCR专家。提取截图中的所有金额数字和关键字段：1)剩余待还/全部待还 2)累计账单金额 3)剩余应还 4)还款记录 5)还款日。只输出数字和字段名。'

    payload = {
        'model': 'Qwen/Qwen3-VL-32B-Instruct',
        'messages': [{
            'role': 'user',
            'content': [
                {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{img}'}},
                {'type': 'text', 'text': prompt}
            ]
        }],
        'stream': False,
        'max_tokens': 1500
    }

    req = urllib.request.Request(
        'https://api.siliconflow.cn/v1/chat/completions',
        data=json.dumps(payload).encode(),
        headers={
            'Authorization': f'Bearer {API_KEY}',
            'Content-Type': 'application/json'
        }
    )

    try:
        resp = json.loads(urllib.request.urlopen(req, timeout=90).read())
        print(f'\n=== 截图 {i+1} ===')
        if 'choices' in resp:
            print(resp['choices'][0]['message']['content'])
        else:
            print(json.dumps(resp, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f'截图{i+1}出错: {e}')
```

## 关键参数
| 参数 | 值 | 说明 |
|------|-----|------|
| timeout | 90s | 大图片解码需要更长时间 |
| model | Qwen/Qwen3-VL-32B-Instruct | 不要用 VL-max 或其他 |
| max_tokens | 1500 | OCR 输出通常 500-1000 tokens |

## env var 不可用的解决路径

### 方案 A：source .env（推荐）
```bash
source /Users/mac/.hermes/profiles/finance/.env && python3 your_script.py
```

### 方案 B：execute_code（继承网关 env）
```python
# 在 execute_code 中直接调用，os.environ 包含所有网关变量
import os; api_key = os.environ['SILICONFLOW_API_KEY']
```

### 方案 C：直接传 key
```bash
python3 -c "
import json, base64, urllib.request
API_KEY = 'sk-xxx...'  # 波总手给的
# ... 如上模板
"
```

## 拿去花 OCR 注意事项（2026-07-22 实测）
- 截图1（账单汇总页）：显示「累计账单金额 ¥17,455.61」和还款记录
- 截图2（当前余额页）：显示「剩余待还 ¥1,266.59」+「还款日 9月21日前」
- 三个不同数字：剩余待还(总负债) ≠ 累计账单金额(本期) ≠ 剩余应还(扣退款后)
- 只有「剩余待还」才是要更新到 debts.json 的数字
