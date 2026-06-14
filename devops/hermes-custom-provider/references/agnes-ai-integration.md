# Agnes AI 接入记录 (2026-06-14)

## 提供商信息
- **公司:** Sapiens AI (母公司)
- **产品:** Agnes AI
- **定价:** 免费
- **文档:** https://docs.agnes-ai.com

## API 配置
- **Base URL:** `https://apihub.agnes-ai.com/v1`
- **认证:** Bearer Token (Authorization header)
- **格式:** OpenAI Compatible
- **注意:** 原始域名 `api.agens.ai` 有 SNI 证书问题，不能用。正确域名是 `apihub.agnes-ai.com`

## 可用模型

| 模型名 | 类型 | 说明 |
|--------|------|------|
| `agnes-1.5-flash` | 文本 | 快速轻量级，中文推理/代码够用 |
| `agnes-2.0-flash` | 文本 | 升级版本，中文能力更强 |
| `agnes-image-2.1-flash` | 图像 | 文生图/编辑 |
| `agnes-image-2.0-flash` | 图像 | 图像生成 |
| `agnes-video-v2.0` | 视频 | 文生视频 |

## 性能基准 (实测)

| 指标 | agnes-1.5-flash | agnes-2.0-flash | DeepSeek Pro |
|------|----------------|-----------------|--------------|
| 延迟 | ~2s | ~2.4s | ~2-3s |
| 中文数学推理 | ✅ 中等偏上 | ✅ | ✅ 深度更高 |
| Python 代码 | ✅ 有类型注解 | ✅ | ✅ 更深度 |
| 金融知识 | ✅ 基本准确 | ✅ | ✅ |
| JSON 结构化 | ✅ | ✅ | ✅ |
| 速度 | 相近/略快 | 相近 | 基准 |

## 已知问题

1. **TLS 证书损坏:** `api.agens.ai` (文档初版写的域名) 有 SNI 问题，无法建立 TLS 连接。必须用 `apihub.agnes-ai.com`。
2. **API Key 不稳定:** 认证间歇性返回 401，即使 key 看起来正确。平台侧问题，非配置问题。可能 key 被重置或并发限流。
3. **模型列表查询不稳定:** `/v1/models` 端点偶尔也返回 401。
4. **Key 精确性:** Key 文件中不能有任何尾随空白字符，精确字节匹配。`echo -n` 写入，无换行。

## 配置建议

波总的目标：免费 Agnes 为主，能力不足时自动升级到 DeepSeek Pro。

实现方式: 在 config.yaml 中设置 agnes 为 `model.default`，并将 deepseek 加入 `fallback_providers`。但需先解决 API key 稳定性问题。

Hermes 原生 `fallback_providers` 只在 API 调用失败时才切换，不是基于质量判断。要实现"质量不够也升级"，需要使用 `smart_model_routing` 或自定义方案。

## API Key (已记录，不在技能文件中)
- 存储在 EverOS / mem0
- 不在 SKILL.md 或 references 中硬编码
