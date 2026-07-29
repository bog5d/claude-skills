# 2026-07-29 ChatGPT 修复会话

## 问题
ChatGPT 连不上 → Cloudflare 403 (cf-mitigated: challenge)

## 诊断步骤
1. 国内网络: ✅ 百度 0.15s
2. 代理 Google: ✅ 200 (1.4s)
3. 代理 ChatGPT: ❌ 403 (1.0s)
4. 直连 ChatGPT: ❌ timeout (GFW)

## 节点发现
从 backup configs 中发现 3 个节点：

| 节点名 | 协议 | Server | UUID | 状态 |
|--------|------|--------|------|------|
| BWG-CN2-Reality | vless | 89.208.247.51:27015 | d7a87084... | 403 |
| CDN-Backup | vmess+ws | node.hellobog.com:80 | 25bf8d24... | 403 |
| VIP-Reality-救命节点 | vless | 67.230.168.235:27015 | d7a87084... | 403 |

**关键发现**：UUID 相同但 server IP 不同 (89.208.247.51 vs 67.230.168.235) → 同一订阅商的不同出口。

## 生成的配置文件
`hermes-chatgpt-fix-20260729.yaml` — 3 节点合并 + URLTest 优选 + 完善 AI 规则

## 程序化导入
1. 创建 `profiles/p_new_fix.yaml` (proxies enhancement)
2. 创建 `profiles/hermes-chatgpt-fix-20260729.yaml` (full config)
3. 创建空 enhancement files (m_, s_, r_, g_)
4. 编辑 `profiles.yaml` → 添加新 profile entry → 切换 current
5. `cp` 到 `clash-verge.yaml` + `clash-verge-check.yaml`
6. POST /restart 重启核心

## 结果
所有节点返回 403 → **订阅商整个 IP 池被 OpenAI Cloudflare 封禁**
