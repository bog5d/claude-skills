---
name: wechat-mini-program-agent
description: 微信小程序AI助手——架构设计、开发部署、知识库对接全流程。波总要把Hermes能力产品化到微信生态的标准方案。
category: devops
trigger: 微信小程序, WeChat AI, 公众号AI, 意图入口, mini program agent
---

# 微信 AI 对话助手 — 架构与开发

## 产品定位

微信小程序形态的AI对话助手。后端接知识库（文章+公司数据），前端极简聊天界面。

核心价值：让波总的读者/投资人在微信里跟文章对话，自己也能快速查公司数据。

## 架构

```
微信小程序(前端) → HTTPS → 阿里云API(后端 47.85.62.133:8788)
                                ├── 知识库(PostgreSQL+pgvector)
                                ├── 文章拉取(WordPress→chunk→embed)
                                └── LLM(DeepSeek/Qwen)
```

## 技术栈

| 层 | 技术 | 说明 |
|----|------|------|
| 前端 | 微信原生框架 / uni-app | 极简聊天界面，就一个对话框+输入框 |
| 后端 | Python FastAPI | 运行在现有阿里云服务器 47.85.62.133 |
| 知识库 | PostgreSQL + pgvector | 文章向量化存储+检索 |
| LLM | deepseek-chat 或 qwen-turbo | 便宜够用 |
| 部署 | systemd + nginx | 与现有 wechat-publisher-relay 共存 |

## MVP 范围

- v0.1：读者能跟历史文章对话（问"意图入口什么意思"→AI基于文章回答）
- v0.2：波总自己能查公司数据（财务/产品/IPO进度）
- 不包含：多轮深度对话、用户画像、推送通知

## 关键 API 设计

```
POST /api/chat      - 对话 {openid, message, history} → {reply, sources}
POST /api/login     - 微信登录 {code} → {token, openid}
GET  /api/articles  - 文章列表
POST /api/admin/ingest - 触发文章拉取
```

## 知识库管道

1. cron 每6小时从 WordPress 拉取新文章
2. 文章分块(chunk 500-1000字) → embed → 存 pgvector
3. 对话时：检索相关 chunk → 拼入 prompt → LLM 回答 → 标注来源

## 风险

- 微信小程序需备案+审核 → 测试号先跑通
- 服务器现有负载 → 先评估 47.85.62.133 资源
- 文章版权 → 回答标注来源，不全篇复制

## 存档

架构设计：`~/.hermes/cache/documents/微信AI助手_架构设计.json`
