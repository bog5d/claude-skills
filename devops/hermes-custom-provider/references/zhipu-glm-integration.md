# Zhipu GLM Integration Record

## Session: 2026-06-21 (her-m2)

### Key Provided
Format: `id.secret` (dot-separated, no `sk-` prefix)
Example: `3b602c8aecb64509a88d160fcbdfe481.7OeAZogoTqA3Awp`

### Environment
- Env var: `GLM_API_KEY`
- Hermes built-in provider: `glm`
- Base URL: `https://open.bigmodel.cn/api/paas/v4/`
- Free model: `glm-4-flash`

### 401 Errors Encountered
Both `openai` compatible mode and `zhipuai` SDK returned:
```
AuthenticationError: Error code: 401 - {'error': {'code': '1000', 'message': '身份验证失败。'}}
```
Possible causes:
1. Key may have been regenerated or revoked after sharing
2. Key may belong to a different platform (not 智谱开放平台)
3. Account may need real-name verification to use API

### Verification Commands
```bash
# OpenAI-compatible mode
python3 -c "
from openai import OpenAI
client = OpenAI(api_key='KEY', base_url='https://open.bigmodel.cn/api/paas/v4/')
print(client.chat.completions.create(model='glm-4-flash', messages=[{'role':'user','content':'hi'}], max_tokens=5).choices[0].message.content)
"

# Zhipu SDK mode
python3 -c "
from zhipuai import ZhipuAI
client = ZhipuAI(api_key='KEY')
print(client.chat.completions.create(model='glm-4-flash', messages=[{'role':'user','content':'hi'}]).data.choices[0].message.content)
"
```

### User Action Required
- Confirm key is from https://open.bigmodel.cn
- May need to regenerate at API Keys page
- Real-name verification may be required on the account
