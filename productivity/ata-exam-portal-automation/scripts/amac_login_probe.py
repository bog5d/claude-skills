#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中基协基金从业报名系统（ATA/ZC-Group 集体用户）登录探测脚本——半自动。
实测于 2026-08-18，全链路可跑通。

用法：
  python3 amac_login_probe.py --account <账号> --password <密码>
  （可选 --url https://baoming.amac.org.cn/ZC-Group/ --api-key <KEY>）

流程：
  1. GET 登录页拿 SERVERID cookie
  2. Connect 拿 requestId
  3. 下载算式验证码到 /tmp/amac_captcha.png
  4. 暂停等你把验证码图片喂给 vision_analyze 识别（如 "57-8=?" → 49）
  5. 输入识别结果 → SignIn → 打印 Code/Message

凭据纪律：不写文件、不落日志、不存仓库；测试完即弃。
锁定纪律："账号不存在"的候选无风险；提示密码错误立即停（连错约5次锁账号）。
"""
import argparse
import json
import os
import sys
import time
import urllib.request
import http.cookiejar

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
DEFAULT_APIKEY = "CF802519-BF29-41F8-82A2-048B5D2F5EEE"


def http_get(url, cookie_jar, headers):
    req = urllib.request.Request(url, headers=headers)
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cookie_jar))
    return opener.open(req, timeout=25).read()


def http_post_json(url, cookie_jar, headers, payload):
    data = json.dumps(payload).encode("utf-8")
    headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cookie_jar))
    return json.loads(opener.open(req, timeout=25).read())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--account", required=True)
    ap.add_argument("--password", required=True)
    ap.add_argument("--url", default="https://baoming.amac.org.cn/ZC-Group/")
    ap.add_argument("--api-key", default=DEFAULT_APIKEY)
    ap.add_argument("--system-name", default="SGZJGrpSite")
    ap.add_argument("--out", default="/tmp/amac_captcha.png")
    args = ap.parse_args()

    base = args.url.rstrip("/")
    # serviceUrl = parent path of 入口 + "Service/"
    # /ZC-Group/ -> /ZC-GroupService/
    svc = base.rsplit("/", 1)[0] + "Service/"
    cj = http.cookiejar.CookieJar()
    headers = {
        "User-Agent": UA,
        "Referer": base + "/",
        "APIKey": args.api_key,
    }

    # 1. 登录页拿 SERVERID
    http_get(base + "/", cj, headers)
    print("[1] cookie 获取完成")

    # 2. Connect 拿 requestId
    raw = http_get(svc + "AuthenticationService/Connect", cj, headers)
    rid = json.loads(raw)["Data"]
    print(f"[2] requestId = {rid}")
    headers[args.system_name + "-CurrentRequestId"] = rid

    # 3. 下载验证码
    ts = int(time.time() * 1000)
    cap_url = (svc + f"CaptchaService/Refresh?APIKey={args.api_key}"
               f"&{args.system_name}-CurrentRequestId={rid}&rnd={ts}")
    img = http_get(cap_url, cj, headers)
    with open(args.out, "wb") as f:
        f.write(img)
    print(f"[3] 验证码已保存: {args.out}（sips -s format png {args.out} 转 PNG 后喂 vision_analyze）")

    # 4. 人工/LLM 识别
    code = input("[4] 请输入 vision 识别出的算式结果（如 49）: ").strip()

    # 5. SignIn
    payload = {
        "LoginAccount": args.account,
        "Password": args.password,
        "ValidateCode": code,
    }
    try:
        result = http_post_json(svc + "AuthenticationService/SignIn",
                                cj, headers, payload)
        print(f"[5] Code: {result.get('Code')}")
        print(f"    Message: {result.get('Message')}")
        if result.get("Data"):
            print(f"    Data: {json.dumps(result['Data'], ensure_ascii=False)[:200]}")
    except Exception as e:
        print(f"[5] 请求异常: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
