# 微信草稿静默截断调试 Playbook（2026-08-22 实战）

## 事故经过

波总发布《我在高铁上，给 AI Agent 搭了一个"网盘"》，公众号后台预览发现**草稿只显示前 1/3**（到第三章"公共文件仓库"就没了），四~八章 + 结尾全丢。发布脚本全程无报错（errcode=0）。

## 调试路径（按序执行）

### 1. 先回读确认截断（不是猜）

```python
# draft/get 拉回实际存储的 content
raw2 = _wechat_post(f"/cgi-bin/draft/get?access_token={token}",
                    json.dumps({"media_id": mid}).encode(),
                    {"Content-Type": "application/json"}, timeout=15)
content = json.loads(raw2)["news_item"][0]["content"]
# 断言：章节标题 + 最后一句
assert "四、我最开始" in content and "写在最后" in content
# 长度对比：发送 ~12KB，回读 6833 → 截断实锤
```

### 2. 对比发送 HTML 与回读 content 找截断点

- 回读 content 尾部 = 截断点。本次尾部是 `<p>比如：</p><p>...</p><p style="display: none;"><mp-style-type data-value="10000">`
- 截断点正好在 ` ```text ` 流程图代码块段落前 → 嫌疑锁定代码块段
- 同时注意：微信会**重排 DOM**（图片位置变了、段落顺序变了）——这是解析器规范化输出，不是 bug，别被误导

### 3. A/B 对照测试隔离元凶（关键手法）

对可疑内容建 2 个临时测试草稿，其余不变：

```python
# 变体A：保留可疑内容（代码块原样）
# 变体B：改造为纯文本段落（去 ``` 和 ↓，换 →）
r = add_draft(content_A, '【测试】A-保留代码块')   # → draft/add
r = add_draft(content_B, '【测试】B-纯文本改造')
# 各自 draft/get 对比：
#   变体A len=11289 完整 ✅ / 变体B len=11269 完整 ✅
# → 结论：代码块不是元凶，draft/add 路径本身没问题！
# 测完 draft/delete 清理（标题带【测试】前缀便于识别）
```

**A/B 结果推翻了"代码块是元凶"的假设** → 转向检查 `draft/update` 路径（因为发布脚本查重后发现同名草稿走了 update，而测试走的是 add）。

### 4. 定位 update 路径双坑

坑一：`draft/update` 的 `articles` 是**对象**，`draft/add` 才是**数组**。传数组 → 47001 data format error（或更隐蔽：errcode=0 但 content 静默不更新，update_time 变了内容没变）。

坑二：update 成功后**不验证** → 旧截断内容残留。修复：update 后 GET 回读，len(saved) < len(sent)*0.9 时删旧重建（draft/delete → draft/add）。

### 5. 根因回溯（本次最终根因）

第一次发布（走 add）其实就被截断——因为当时的 HTML 里有**孤立 `</div>`**：`strip_layout_image_blocks()` 非贪婪正则 `<div class="wechat-image-block">.*?</div>` 只删到 caption 的闭合标签，**残留外层 `</div>`**。微信解析器遇无配对开标签的 `</div>`，把其后所有节点丢弃。

修复：
```python
block_pattern = re.compile(r'<div class="wechat-image-block">.*?</div>\s*</div>', re.S)
while prev != html:          # 循环清理嵌套
    prev = html
    html = block_pattern.sub("", html)
html = re.sub(r'<img[^>]*>', '', html)
```

## 发布后验证脚本（每次发布必跑）

```python
# 关键断言
assert len(content) > 8000                    # 长度下限（微信会把空壳裁掉）
for kw in ['一、', '二、', '三、', '四、', '五、', '六、', '七、', '八、', '写在最后', '<最后一句关键词>']:
    assert kw in content
```

## 其他坑（本次顺带发现）

- **thumb_media_id 从 draft/get 回读为空**（微信只给 `thumb_url`）：做测试草稿时需 `material/add_material` 重传封面拿新 media_id，否则 40007
- **media_id 只能从完整返回值拿**：日志截断的 `bQqYgPWs61_ROOqZBKIh...` 不能用于请求，从 `draft/batchget` 回读完整值
- **skill 文档"声称已修"不可信**：wechat-publish-direct 的 bug 表 #8/#10 声称 2026-07-07 修复，但代码里从未落地。改完代码必须 grep 验证修复真在
