---
name: cloud-browser-download
description: Use when 网盘下载URL绑定IP、本机curl 403。云浏览器CDP拦截响应体取文件。
version: 1.0.0
author: Hermes Agent (curator consolidation)
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [download, cloud-browser, firecrawl, cdp, 123pan, anti-scraping]
    related_skills: [123pan-download, cloud-browser-setup]
category: devops
trigger: 从云浏览器（firecrawl interact / Browserbase）下载网盘/受保护文件；123pan 分享链接下载；本机 curl 下载网盘文件 403
priority: normal
---

# 云浏览器下载受反爬/IP 绑定保护的文件

## When to Use

- 网盘分享（123pan 等）的下载 URL 需要从浏览器会话获取，且**本机 curl 下载失败 403**
- 浏览器工具不可用（无 browser_navigate/browser_console 类工具），但 firecrawl interact 可用（返回 `cdpUrl`）
- 123pan-download 技能的"浏览器拦截 + 本机 curl"路径走不通时（见下）

## 核心坑：下载签名与 IP 绑定

123pan 等网盘的下载 URL（`dispatchList[0].prefix + downloadPath`）带签名参数（`s`/`t`/`bzs`），**与获取签名时的客户端 IP 绑定**。云浏览器拿到的 URL 只能在云浏览器同 IP 下请求；本机 curl 必然：

```
HTTP 403 Forbidden
{"code":1010,"message":"download err: 50001"}
```

带 Referer/Cookie/UA 均无效（cookie 可能为空域、IP 绑定不依赖 cookie）。**判定：签名 URL 来自云浏览器 → 不要本机 curl，直接从浏览器会话侧取响应体。**

其他无效路径（均实测失败）：
- 页面上下文 `fetch(downloadUrl)` → CDN CORS 拦截 `Failed to fetch`
- `Network.getCookies` 取 cookie 带 curl → cookie 可能为空 + 对 IP 绑定无帮助

## 可行方案：CDP Fetch 域拦截响应体

云浏览器（firecrawl interact）返回 `cdpUrl`（`wss://browser.xxx/cdp/<id>?token=...`），可直接用 Python `websockets` 连接：

1. 连接 CDP，`Target.getTargets` 找目标页面 target（按 URL 含站点域匹配），`Target.attachToTarget`（flatten: true）拿 `sessionId`。
2. 对 session 启用 `Network.enable` + `Fetch.enable`（patterns: `[{"urlPattern": "*cjjd19.com*", "requestStage": "Response"}, {"urlPattern": "*123295.com*", "requestStage": "Response"}]`——按目标 CDN 域调整）。
3. 通过 `Runtime.evaluate` 在页面点"浏览器下载"按钮（`[...document.querySelectorAll('button,span,div,a')].filter(x => x.textContent.trim()==='浏览器下载' && x.offsetParent!==null)[0].click()`）。
4. 事件循环收 `Fetch.requestPaused` → `Fetch.getResponseBody(requestId)`（base64Encoded）→ `Fetch.continueRequest` 放行。
5. base64 解码写盘 → `file` 确认类型（123pan zip 伪装常见）→ Windows 上传 zip 中文名用 cp437→gbk 解码（Python zipfile 逐项改名再 extract）。

现成脚本：`scripts/123pan_cdp_fetch.py`（改 `CDP_URL` + 页面 URL 匹配子串后直接跑）。

## 陷阱

- CDP URL 有时效，长任务前先确认会话还活着（getTargets 能返回）。
- 下载前缀（prefix）约 5 分钟时效：拦截响应体方案不受影响（响应体在会话内流式返回），但多次重试失败后应重新点击"浏览器下载"刷新签名。
- `Fetch.getResponseBody` 对超大文件（>几十 MB）可能失败；小文件（<1MB）稳定。超大文件改用 `Page.setDownloadBehavior` + 容器文件导出（依赖云浏览器平台能力）。**实测 110KB zip 稳定，且 `websockets.connect(CDP_URL, max_size=300*1024*1024)` 必须设大，否则大文件 base64 帧直接断开。**
- **点击"浏览器下载"后第一个被 Fetch 拦截的往往是统计请求**（如 `matomo.php`，`getResponseBody` 返回 0 bytes）——忽略它，继续等下一个请求（真正的 CDN 下载请求 body 字节数=文件大小）。也可用 `Network.responseReceived` 的 status==200 + URL 含 CDN 域来识别真下载。
- websockets 库：`import websockets`（异步）；CDP 消息循环要处理 `id` 匹配 + 事件（无 id 的消息是事件），用 `sessionId` 区分。
- 变量命名别用 `CDP` 当类名同时当 URL 常量（`urllib.parse.urlparse` 报 `type object has no attribute 'decode'`）。
- **IP 绑定判定扩展**：不仅 curl 403，本机任何非浏览器会话的下载尝试（带 cookie/UA 也无效）都 403——直接走 Fetch 拦截，不要浪费轮次试 cookie 方案。
