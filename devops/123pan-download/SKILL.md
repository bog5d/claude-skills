---
name: 123pan-download
description: 从123云盘分享链接下载文件的可靠工作流。使用浏览器拦截方式获取经过深度混淆的下载URL。支持有密码和无密码分享，支持单个文件和批量下载。
---

# 123云盘文件下载

## 背景

123云盘是中国网盘服务，分享链接有强反爬保护：下载URL经过前端JS动态签名、多次302跳转、时间戳校验。curl/requests等简单HTTP工具几乎总是失败（返回 `code:-3 "文件夹内无可下载内容"`）。

唯一可靠的方式是通过**浏览器拦截**下载API的响应，从中提取真实下载URL。

## 工作流

### Step 1: 打开分享页

```python
browser_navigate(url="https://xxx.share.123pan.cn/...?pwd=XXXX")
```

如果页面有提取码输入框（`textbox`+`button`），点击提取按钮。

### Step 2: 注入网络拦截器

在点击"浏览器下载"之前，先在 `browser_console` 中注入拦截器。**注意：必须同时记录所有 fetch URL 到 `__allFetches` 数组**，因为首次点击"浏览器下载"可能只触发 `download/info`（斜杠形式），而真正的 `dispatchList` 在下一次请求中返回。

```javascript
var _f = window.fetch;
window.__allFetches = [];
window.fetch = function() {
  var url = typeof arguments[0] === 'string' ? arguments[0] : arguments[0]?.url || '';
  window.__allFetches.push(url);
  return _f.apply(this, arguments).then(function(r) {
    // Match both /download/info (slash) and /download_info (underscore) patterns
    if (url.includes('download')) {
      var c = r.clone();
      c.text().then(function(t) {
        var trimmed = t.trim();
        if (trimmed.includes('dispatchList')) {
          window.__dlInfo = trimmed;
        }
      });
    }
    return r;
  });
};
```

⚠️ **重要：上述拦截器只在注入后才生效**——如果第一次点击"浏览器下载"时拦截器尚未注入，dispatchList 不会被捕获。此时需要关闭弹窗 → 重新点击"浏览器下载" → 重新点击"备用下载线路"。

### Step 3: 触发下载

1. `browser_click` 点击"浏览器下载"按钮
2. 弹窗出现后，`browser_click` 点击"备用下载线路"
3. 用 `browser_console` 检查 `window.__dlInfo` 是否包含 dispatchList
4. 如果 `window.__dlInfo` 为 null 或只包含 `vipType` 而不含 `dispatchList`：关闭弹窗，重新点击"浏览器下载"→"备用下载线路"

### Step 4: 提取下载URL（走 console 日志，不走 `window.__dlInfo`）

如果 `window.__dlInfo` 多次覆盖仍未捕获到 `dispatchList`，**从 `browser_console()` 的日志输出中手动提取**。console 日志中会包含完整的下载信息：

```
CAPTURED DOWNLOAD: {"code":0,...,"data":{"dispatchList":[{"prefix":"https://...","isp":"下载线路一"},...],"downloadPath":"/1135-guest-share-free-download-cdn.123295.com/..."}}
```

注意：`downloadPath` 在日志中可能被截断（超 1000 字符）。用完整的 prefix + downloadPath 拼接 URL。

### Step 4: 提取下载URL

响应JSON格式：
```json
{
  "code": 0,
  "data": {
    "dispatchList": [
      {"prefix": "https://xxx.pd1.cjjd19.com", "isp": "下载线路一"},
      {"prefix": "https://xxx.pd2.cjjd19.com", "isp": "下载线路二"}
    ],
    "downloadPath": "/1135-guest-share-free-download-cdn.123295.com/batch-download/...?v=5&t=..."
  }
}
```

完整下载URL = `dispatchList[0].prefix` + `downloadPath`

### Step 5: 用curl下载

```bash
curl -L -o output_file.zip "https://prefix.xxx.com/path?..."
```

或者用Python requests（带超时，大文件可能需要几分钟）。

## 参数分析

- `shareKey`: URL路径中的 share ID（如 `kKz0vd-3Pj4h`）
- `sharePwd`: 提取码
- 拦截到的API调用通常是：`/b/api/v2/file/batch_download_share_info`
- 同一个页面会先调用 `/b/api/share/download/traffic/check` 进行流量检查

## 常见失败模式

| 错误 | 原因 | 解决 |
|------|------|------|
| `code:-3` 无可下载内容 | 缺少正确session/token | 确保在浏览器中已先访问分享页，用浏览器拦截而非curl直调 |
| `code:-3` 刷新后重试 | 签名参数过期 | 重新打开分享页再试 |
| curl下载为0字节 | 302跳转未跟随 | 检查 `curl -L` 是否启用 |
| 下载到的是HTML页面 | URL被防盗链拦截 | 检查 `Referer` 头是否正确 |
| 第一次点击`window.__dlInfo`无dispatchList | 拦截器注入晚于第一次API调用 | 关闭弹窗重新点击"浏览器下载"→"备用下载线路" |
| `window.__dlInfo`被流量检查覆盖 | `traffic/check`也包含"download" | 只保存包含`dispatchList`的响应，过滤掉无dispatchList的 |
| console日志中downloadPath被截断 | console.log默认截断 | 从日志中分段拼接，或用`browser_console`执行 `JSON.parse(window.__dlInfo).data.dispatchList[0].prefix + JSON.parse(window.__dlInfo).data.downloadPath` 获取完整URL |
| screencapture/截图失败 | sandbox无display | 用Swift+KVC的方式截屏（`CGDisplayCreateImage` via `dlopen`） |

## 已知坑点

- 下载线路前缀(prefix)有时效性（约5分钟），获取后尽快下载
- **上传/login 被反爬拦截**：浏览器登录（手机号+密码）在高概率被反爬检测拦截（Browserbase 环境）。即使填写正确账号密码，点击登录后页面无反应或重复显示登录表单。123云盘的登录接口有强反爬机制（passport 加密），非真实用户环境几乎无法绕过。**回传文件优选 Telegram 拆分发送或百度网盘，不要在 123pan 登录上传上浪费时间。**
- 同一个分享URL的 `dispatchList` 每次请求可能会变
- 文件可能被命名为 `.jpg` 实际是zip（123云盘对zip文件做了伪装），下载后用 `file` 命令确认
- 各分享文件的 `downloadPath` 完全不同，无法复用
- 123云盘有频率限制：多次重新请求同一文件会被临时封禁
- **Windows ZIP 中文文件名乱码（血坑）**：从 Windows 上传的 ZIP 文件，在 macOS 上用 `unzip` 解压时中文文件名/目录名会变成乱码（`Illegal byte sequence`）。这是因为 ZIP 使用 CP437 编码存储文件名，需要用 Python 的 `zipfile` 指定 GBK 解码：

```python
import zipfile
with zipfile.ZipFile('archive.zip', 'r') as z:
    for info in z.infolist():
        try:
            name = info.filename.encode('cp437').decode('gbk')
        except:
            name = info.filename  # fallback
        info.filename = name
        z.extract(info, 'extracted/')
```

- **文件名截断注意**：123云盘批量下载时 ZIP 内文件可能嵌套多层（如 `talant_hub（人才联盟）/Talant_Hub/02_Raw_Data/...`），解压后用 `find . -type f | head -40` 快速查看结构，不要只看顶层目录。**中文目录名在 ZIP 列表（`unzip -l`）中显示为问号是正常的，用 Python 解压即可正确解码。**

## 备选方案

如果浏览器拦截失败或无法使用浏览器：

### 方法B: 用户直接传文件
让用户把文件通过即时通讯工具直接发来。这是最终的保底方案。

### 方法C: 用开源CLI工具
有一些第三方123pan CLI客户端（如 `123pan-cli`、`123pan` npm包），但不稳定且需登录账号密码，不推荐在自动化流程中使用。