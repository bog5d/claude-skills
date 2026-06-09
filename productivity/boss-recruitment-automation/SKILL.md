---
name: boss-recruitment-automation
description: BOSS直聘招聘自动化——登录、简历批量下载、六维打分排序。用于波总在BOSS直聘发布职位后筛简历的场景。
version: 1.0.0
triggers:
  - 用户说"BOSS直聘 自动化 下载简历 打分 排序 筛人 招聘"
  - 用户提到投融资助理岗位的简历筛选
---

# BOSS 直聘招聘自动化

从 BOSS 直聘登录 → 批量获取简历 → AI 六维打分 → 排名输出，全链路自动化。

---

## 前置条件

- macOS + 有人能在电脑前（需要扫码登录）
- Playwright 已安装（`pip3 install playwright && python3 -m playwright install chromium`）
- 用户已在 BOSS 直聘发布了职位

---

## 流程

### Phase 1: 确认 JD 和筛选标准

1. 从对话中提取岗位要求（学习力、专业力、商务力、销售属性、抗压、开放心态六个维度）
2. 确认权重和红线淘汰条件
3. 输出 JD 草稿让用户确认
4. JD 和标准确认后，打分引擎已内置在 `scripts/boss_resume_scorer.py`

### Phase 2: 登录 BOSS 直聘

**关键坑：BOSS 直聘反 headless 极强，必须用非 headless 模式。**

1. 写 Playwright 脚本，必须设置 `headless=False`
2. 导航到 `https://www.zhipin.com/web/user/?ka=header-login`
3. 截图发用户（让电脑前的人确认屏幕上有二维码）
4. 用户远程扫码（微信视频/FaceTime 对着屏幕）
5. 脚本检测 URL 跳转到 chat/geek/recommend/campus 即登录成功
6. 保存 `storage_state` 到 `~/.hermes/cache/boss_session.json`

**如果截图是白屏（5KB 左右）：**
- Mac 可能锁屏/休眠了 → 让电脑前的人唤醒 Mac
- 如果白屏持续 → 考虑让用户手动在电脑上打开 Chrome 登录，导出 cookie

### Phase 3: 自动化翻页 + 提取简历

1. 加载 `boss_session.json` 恢复登录态
2. 导航到简历管理页面
3. 翻页遍历候选人列表
4. 点击每个候选人，提取简历文本
5. 保存到 `~/boss_resumes/` 目录（JSON 格式）

### Phase 4: 打分排序

运行 `scripts/boss_resume_scorer.py`:
```bash
python3 ~/.hermes/scripts/boss_resume_scorer.py ~/boss_resumes/all_resumes.json
```

输出：六维打分 + 加权总分 + 排名表，淘汰的单独标注。

---

## 打分引擎说明

脚本路径：`~/.hermes/scripts/boss_resume_scorer.py`

六维权重（可在脚本中调整）：
- 学习力 25% / 专业力 20% / 商务力 20% / 销售属性 15% / 抗压 10% / 开放心态 10%

红线命中直接淘汰（社恐、排斥社交、玻璃心等关键词）。

---

## 已知反爬对抗

| BOSS 直聘防御 | 我们的对策 |
|-------------|----------|
| headless 检测 | `headless=False`，开真实 Chrome 窗口 |
| `navigator.webdriver` | `add_init_script` 覆盖 |
| IP 频率限制 | 操作间加 `wait_for_timeout` |
| 登录态过期 | 重新扫码刷新 session |

---

## 相关文件

- `scripts/boss_resume_scorer.py` — 六维打分引擎
- `scripts/boss_show_qr.py` — 登录页弹出 + 截图
- `~/.hermes/cache/boss_session.json` — 登录态存储
- `~/.hermes/cache/documents/boss_qrcode.png` — 登录页截图
