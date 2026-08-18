---
name: ata-exam-portal-automation
description: 用 curl 逆向登录 ATA 考试报名系统（中基协基金从业等），含验证码识别与账号体系坑。
---

# ATA 考试报名系统登录自动化（基金从业等）

## 适用场景
- 波总要测试中基协基金从业考试报名账号（集体用户/个人）能否登录
- 报名窗口期自动化查状态、集体预报名（行业专场）
- 同框架系统可复用：中证协证券从业、中注协等 ATA(全美在线) 承办的报名系统

## 系统架构（已逆向，2026-08-18 实测）

- 域名：baoming.amac.org.cn
- 入口：`/ZC-Group/`（集体用户/机构，模块名 `etxgrp`）、`/ZC-Site/`（个人考生）
- 前端：AngularJS SPA，`$script` 加载 EtxWeb.min.js + extras.min.js，`angular.bootstrap(document,['etxgrp'])`
- **关键常量**（在 extras.min.js 里挖）：
  - `SystemName = "SGZJGrpSite"`（请求头前缀）
  - `serviceUrl = "/ZC-GroupService/"`
  - `APIKey = "CF802519-BF29-41F8-82A2-048B5D2F5EEE"`（全局默认头 `$http.defaults.headers.common.APIKey`，**缺了报 -99 没有合法授权认证**）
- 登录服务：`AuthenticationService`（Connect / SignIn / SignOut）
- 验证码：`CaptchaService/Refresh`，**算式图片**（GIF 300x72，如"57-8=?"），可用 vision_analyze 识别

## 登录流程（curl 五步，全部实测可跑通）

```bash
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
APIKEY="CF802519-BF29-41F8-82A2-048B5D2F5EEE"
BASE="https://baoming.amac.org.cn"
cd /tmp && rm -f zc_cookies.txt

# 1. GET 登录页拿 SERVERID cookie（必须，否则后续全挂）
curl -sk -c zc_cookies.txt -A "$UA" "$BASE/ZC-Group/" -o /dev/null

# 2. Connect 拿 requestId（必须带 APIKey 头！）
RID=$(curl -sk -b zc_cookies.txt -A "$UA" -H "Referer: $BASE/ZC-Group/" -H "APIKey: $APIKEY" \
  "$BASE/ZC-GroupService/AuthenticationService/Connect" | python3 -c "import sys,json;print(json.load(sys.stdin)['Data'])")

# 3. 下载算式验证码
curl -sk -b zc_cookies.txt -A "$UA" -H "Referer: $BASE/ZC-Group/" -H "APIKey: $APIKEY" \
  -H "SGZJGrpSite-CurrentRequestId: $RID" \
  "$BASE/ZC-GroupService/CaptchaService/Refresh?APIKey=$APIKEY&SGZJGrpSite-CurrentRequestId=$RID&rnd=$(date +%s)000" -o zc_captcha.png

# 4. 用 vision_analyze 识别算式（"57-8=?" → 49），sips 转 PNG 后喂给视觉模型

# 5. 提交登录
curl -sk -b zc_cookies.txt -A "$UA" -H "Referer: $BASE/ZC-Group/" -H "APIKey: $APIKEY" \
  -H "SGZJGrpSite-CurrentRequestId: $RID" -H "Content-Type: application/json" \
  -X POST "$BASE/ZC-GroupService/AuthenticationService/SignIn" \
  -d '{"LoginAccount":"<账号>","Password":"<密码>","ValidateCode":"<识别结果>"}'
```

## 响应码解读
- `Code: 0` → 登录成功（Data 含 Token/ViewName）
- `Code: -1, "账号不存在或已失效"` → 账号不存在（无锁定风险，可放心测下一个候选）
- 密码错误 → 返回密码错误类 message（**有锁定风险，立即停**）
- `Code: -99` → 授权认证失败：检查 APIKey 头 / SERVERID cookie 是否在

## 关键坑（全部实测踩过）

1. **账号体系三分离**（波总最容易搞混的）：
   - 从业人员管理平台 human.amac.org.cn（机构管理员账户）— 管从业人员，**不是**报名账号
   - AMBERS 系统 — 机构/产品备案，也不是
   - 考试报名系统 baoming.amac.org.cn 集体用户 — 才是报名账号
   - 实测：从业平台能登的账号 chunyuejijin 在报名系统报"账号不存在"——两套独立体系，账号不通用
2. **登录框支持两种账号**：`集体用户名` **或 `集体负责人证件号码`**（placeholder 原文）——证件号登录是常见解法
3. **锁定风控**：连续错密码约 5 次锁账号（银行级风控）→ 只测高置信组合；"账号不存在"的候选无风险，密码错即停手
4. 行业专场报名规则：**个人不可报**，机构用集体用户做预报名；61元/科；考前约 1 个月开报（9 月专场≈8 月中下旬窗口，以 amac.org.cn 考试通知栏公告为准）
5. 验证码一次一图，识别错可刷新重试（刷新验证码不消耗密码尝试次数）
6. 客服专线：021-61948893（报名系统）

## 支持文件
- scripts/amac_login_probe.py — 半自动探测脚本：Connect→下载验证码→等你贴入 vision 识别结果→SignIn→打印结果
