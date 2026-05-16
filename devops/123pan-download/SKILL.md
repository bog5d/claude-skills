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

在点击"浏览器下载"之前，先在 `browser_console` 中注入拦截器：

```javascript
var stored = [];
var _f = window.fetch;
window.fetch = function() {
  var url = typeof arguments[0] === 'string' ? arguments[0] : arguments[0]?.url || '';
  return _f.apply(this, arguments).then(function(r) {
    if (url.includes('batch_download') || url.includes('download_info') || url.includes('download_share')) {
      var c = r.clone();
      c.text().then(function(t) { 
        window.__dlInfo = t;  // Capture the JSON response
      });
    }
    return r;
  });
};
```

### Step 3: 触发下载

点击"浏览器下载"按钮（通过ref），再在弹出的dialog中点击备用下载线路。

此时 `window.__dlInfo` 会包含API响应。

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
| screencapture/截图失败 | sandbox无display | 用Swift+KVC的方式截屏（`CGDisplayCreateImage` via `dlopen`） |

## 已知坑点

- 下载线路前缀(prefix)有时效性（约5分钟），获取后尽快下载
- 同一个分享URL的 `dispatchList` 每次请求可能会变
- 文件可能被命名为 `.jpg` 实际是zip（123云盘对zip文件做了伪装），下载后用 `file` 命令确认
- 各分享文件的 `downloadPath` 完全不同，无法复用
- 123云盘有频率限制：多次重新请求同一文件会被临时封禁

## 备选方案

如果浏览器拦截失败或无法使用浏览器：

### 方法B: 用户直接传文件
让用户把文件通过即时通讯工具直接发来。这是最终的保底方案。

### 方法C: 用开源CLI工具
有一些第三方123pan CLI客户端（如 `123pan-cli`、`123pan` npm包），但不稳定且需登录账号密码，不推荐在自动化流程中使用。