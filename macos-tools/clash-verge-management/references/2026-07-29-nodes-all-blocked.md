# 2026-07-29 全部节点被封 — 处理记录

## 问题
用户 ChatGPT 连不上，3个代理节点全返回 403 (cf-mitigated)。

## 已尝试的解法

### 1. 切换配置文件
遍历所有 5 个 profile（配置文件.yaml、config6新ip.yaml、config7新claud、0712、hermes-stable）
→ 所有节点共享同一订阅源，节点池相同

### 2. 发现旧 IP 节点
从「配置文件.yaml」（最早版本）发现 server: 67.230.168.235 的 VLESS Reality 节点
→ 与当前 BWG-CN2-Reality 共用相同 UUID 和 public-key
→ 测试结果：也 403，被封

### 3. 创建并导入新配置文件
- 生成含 3 节点的合并配置 hermes-chatgpt-fix-20260729.yaml
- 使用 URLTest 而非 Fallback（自动选最优节点，50ms tolerance）
- 通过直接编辑 profiles.yaml + cp clash-verge.yaml + API restart 导入

### 4. 浏览器备用
- `open -a Safari 'https://chatgpt.com'` — 浏览器可过 Cloudflare JS challenge
- 但 cua-driver 断连，无法进一步操作浏览器

## 关键教训

### profiles.yaml 编辑法（替代 GUI）
1. 创建 profile YAML → profiles/<name>.yaml
2. 创建 enhancement files (m_/s_/r_/p_/g_)
3. Python yaml.safe_load → append item → yaml.dump 写入 profiles.yaml
4. cp 到 clash-verge.yaml + clash-verge-check.yaml
5. curl -X POST --unix-socket /tmp/verge/verge-mihomo.sock http://localhost/restart

### 同 UDP 不同 server IP 判断
相同 UUID + 相同 public-key + 不同 server IP → 同一订阅商的多出口，非独立节点。
IP 声誉是共享的：一个被封 = 全被封。

### cua-driver 寿命
cua-driver serve 运行 9+ 天后，MCP bridge 断连。
重启方法：kill serve + kill MCP → restart both in background mode.
