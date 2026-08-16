#!/usr/bin/env python3
"""123pan 云浏览器下载：CDP Fetch 域拦截下载请求，从浏览器侧取响应体写盘。

用法：
1. 用 firecrawl interact（或任何返回 cdpUrl 的云浏览器）打开 123pan 分享页，拿到 cdpUrl。
2. 把 CDP_URL 与 PAGE_MATCH 改成实际值，运行本脚本。
3. 脚本自动：找页面 target → 启用 Fetch 拦截（cjjd19.com / 123295.com CDN 域）→ 点"浏览器下载" → 取响应体 → base64 写盘。

原理：123pan 下载 URL 签名与获取 IP 绑定，本机 curl 必 403；必须从浏览器会话侧取。
"""
import asyncio, json, base64, sys

CDP_URL = "wss://browser.xxx/cdp/<id>?token=..."   # ← 改为 firecrawl interact 返回的 cdpUrl
PAGE_MATCH = "123pan"                                # ← 页面 URL 匹配子串
OUT_PATH = "/tmp/123pan_files/downloaded.bin"        # ← 输出路径
BUTTON_TEXT = "浏览器下载"                            # ← 按钮文案（123pan 标准）

CLICK = """
(function(){
  var els = [...document.querySelectorAll('button,span,div,a')];
  var b = els.filter(x => x.textContent.trim() === '%s' && x.offsetParent !== null);
  if (b.length) { b[0].click(); return 'clicked'; }
  return 'not_found';
})()
"""

async def main():
    import websockets
    async with websockets.connect(CDP_URL, max_size=300*1024*1024) as ws:
        mid = 0
        def next_id():
            nonlocal mid; mid += 1; return mid
        async def send(method, params=None, session=None):
            i = next_id()
            msg = {"id": i, "method": method, "params": params or {}}
            if session: msg["sessionId"] = session
            await ws.send(json.dumps(msg))
            while True:
                r = json.loads(await ws.recv())
                if r.get("id") == i:
                    return r.get("result", {})
        async def ev(expr, session=None):
            r = await send("Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True}, session)
            if "exceptionDetails" in r:
                return "EXC: " + json.dumps(r["exceptionDetails"], ensure_ascii=False)[:200]
            return r.get("result", {}).get("value")

        targets = (await send("Target.getTargets")).get("targetInfos", [])
        pages = [t for t in targets if t.get("type") == "page"]
        target = next((t for t in pages if PAGE_MATCH in (t.get("url") or "")), pages[-1])
        att = await send("Target.attachToTarget", {"targetId": target["targetId"], "flatten": True})
        sess = att["sessionId"]
        print("TARGET:", target.get("url"), file=sys.stderr)

        await send("Network.enable", session=sess)
        await send("Fetch.enable", {
            "patterns": [
                {"urlPattern": "*cjjd19.com*", "requestStage": "Response"},
                {"urlPattern": "*123295.com*", "requestStage": "Response"},
            ],
            "handleAuthRequests": False,
        }, session=sess)

        print("CLICK:", await ev(CLICK % BUTTON_TEXT, sess), file=sys.stderr)

        saved = None
        deadline = asyncio.get_event_loop().time() + 40
        while asyncio.get_event_loop().time() < deadline:
            try:
                msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=8))
            except asyncio.TimeoutError:
                print("no more events", file=sys.stderr); break
            m = msg.get("method", "")
            if m == "Fetch.requestPaused":
                rid = msg["params"]["requestId"]
                url = msg["params"]["request"]["url"]
                print(f"PAUSED: {url[:110]}", file=sys.stderr)
                try:
                    body = await send("Fetch.getResponseBody", {"requestId": rid}, session=sess)
                    b64 = body.get("body", "")
                    saved = base64.b64decode(b64) if body.get("base64Encoded") else b64.encode()
                    print(f"GOT BODY {len(saved)} bytes", file=sys.stderr)
                except Exception as e:
                    print(f"getResponseBody fail: {e}", file=sys.stderr)
                await send("Fetch.continueRequest", {"requestId": rid}, session=sess)
        if saved:
            with open(OUT_PATH, "wb") as f:
                f.write(saved)
            print(f"OK {len(saved)} bytes -> {OUT_PATH}")
        else:
            print("NO BODY CAPTURED")

asyncio.run(main())
