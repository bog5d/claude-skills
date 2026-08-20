# 静默 watchdog — 配方与实例

## 可复用脚本骨架（Python stdlib，无第三方依赖）

结构要点（完整可跑版本见 `~/.hermes/profiles/her-m2/scripts/amac_exam_watch.py`）：

```python
# 1. 状态文件 + 日志（都在 ~/HermesBackground/）
STATEFILE = os.path.join(os.path.expanduser("~"), "HermesBackground", "xxx-watch.state.json")
LOGFILE   = os.path.join(os.path.expanduser("~"), "HermesBackground", "xxx-watch.log")

# 2. 带重试的 fetch（urllib，跳过 SSL 校验；只 GET，不登录不提交）
def fetch(url, timeout=25):
    ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
    for attempt in range(3):   # 最多 3 次
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                return r.status, r.geturl(), r.read(500000), None
        except urllib.error.HTTPError as e:
            return e.code, url, e.read(500000), "HTTP %s" % e.code
        except Exception as e:
            if attempt == 2: return None, url, b"", "%s: %s" % (type(e).__name__, e)
            time.sleep(2)

# 3. decode 依次试 utf-8 / gb18030 / gbk
def decode(body):
    for enc in ("utf-8", "gb18030", "gbk"):
        try: return body.decode(enc)
        except Exception: continue
    return body.decode("utf-8", errors="replace")

# 4. 状态机（关键）
st = load_state()                       # {} 表示首跑
has_state = "level" in st
prev_level = st.get("level", 0)

# 门控：非 critical 只在 09:00/15:00 完整探测
if not force and prev_level < 2 and now.hour not in (9, 15):
    return 0                            # 静默跳过，零请求

# 5. 通知决策
if not has_state:
    notify = "seed-baseline"            # 首跑：只落状态，绝不通知
elif level != prev_level or a_url_changed:
    message = build_alert(...)          # 变化：立即发
elif level == 0 and since_last_notify >= 3d:
    message = build_minimal(...)        # 无变化：每 3 天极简
else:
    message = None                      # 静默

if message: print(message)              # 非空 stdout → cron 投递；空 → 静默
save_state({...})
append_log("%s | A=... | B=... | urls=... | level=%d" % ...)

# 6. 顶层兜底
if __name__ == "__main__":
    try: sys.exit(main())
    except Exception:
        append_log("EXCEPTION " + traceback.format_exc()); sys.exit(0)
```

## 无头 Chrome 渲染 JS 页面（macOS）

```bash
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
TMPD=$(mktemp -d)
"$CHROME" --headless --disable-gpu --no-first-run --no-default-browser-check \
  --user-data-dir="$TMPD" --virtual-time-budget=12000 --dump-dom "URL" 2>/dev/null
rm -rf "$TMPD"
```

坑：
- 用旧 `--headless` 旗标（`--headless=new` 在 subprocess 里易报错/超时）。
- `--dump-dom` 打印 DOM 后 Chrome **常不干净退出（挂住）** → 外层加硬 `timeout`，读部分输出即可，别等它 exit。
- stderr 的 `CVDisplayLinkCreateWithCGDisplay failed` 无害（无显示环境），重定向掉。
- 每次用独立 `--user-data-dir`（`mktemp -d`），避免与已开 Chrome 冲突。

## 实例：AMAC 2026年9月基金从业考试（行业专场）集体报名监控（2026-08-20 实录）

任务：盯「9月行业专场」集体报名是否开放；只监控，不注册/不登录/不代报名。

**Part A（公告）— 权威源可静态抓**：
- 考试通知 `https://www.amac.org.cn/fwdt/wyb/rygl/cyks/cykstz/`
- 通知公告 `https://www.amac.org.cn/xwfb/tzgg/`
- 两者是静态 HTML（各 300+ `<a>`），urllib 可抓，正则匹配标题：
  `含"2026" + "9月"/"九月" + ("专场"/"基金从业"/"考试") + ("公告"/"报名"/"通知")`
  → 命中即"当期公告已发"；否则只有年度计划/大纲修订（不算）。

**Part B（网站）— baoming.amac.org.cn 现状**：
- 根域名是 JS 跳转页（257 字节，`window.location = "JJKSreg/page.htm"`），不是维护页。
- 静态落地页（权威信号，非 SPA）：
  - `/zc/page.htm`（专场）→ 显示「个人登录 / 集体登录」按钮 = 可打开
  - `/JJKSreg/page.htm`（通用，根跳转目标）→ 同样有登录按钮
  - 若这些落地页出现「维护/系统维护」文案 → 维护中
- 登录入口命名（都返回 200）：
  - 集体：新 `ZC-Group`（当前专场页指向）、旧 `CZSB30-Group`
  - 个人：新 `ZC-Site`、旧 `CZSB30-Site`
- 登录页本身是 JS SPA（Vue），urllib 只拿到空壳 + title「基金从业人员资格考试网上报名」。

**判定结论（实测）**：网站"可打开但报名未开"（落地页有按钮、无维护字样、公告未出）。用户原说"维护中"与实测冲突 → 无头 Chrome 复核确认为"可打开"，按实测设基线（level=1）。

**通知约定**：变化时标题 `【9月专场】报名有变化`，正文含结论一句话、公告链接、报名起止/考试日、各 URL 状态、下一步该点哪、以及"不登录/不代报名"。
