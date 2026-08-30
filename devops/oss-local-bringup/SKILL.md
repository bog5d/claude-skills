---
name: oss-local-bringup
description: 波总说"开干/跑通/本地部署 XX 开源项目"时使用：clone→依赖→构建→启动通用流程与 Node 26 坑位表。
---

# OSS 本机跑通通用流程 (oss-local-bringup)

## When to Use

波总看了视频/文章里的开源项目后说「开干」「跑通」「部署到本地」。适用任何 GitHub 仓库在本机从零到可运行的完整流程。

## 标准流程

1. **先核实再动手**：web_search 确认仓库真实存在、活跃度(stars/最近提交)、README 的安装节。视频/二手转述里的项目名经常有出入（实例：视频说 "Apache Maca"，实际是 Apache Maka）。
2. **clone 到统一目录**：`git clone --depth 1 <url>` 到 `/Users/mac/oss-lab/<repo>`。
3. **前置环境检查**（一条命令查齐）：`node -v; npm -v; which <README要求的CLI>; docker info --format '{{.ServerVersion}}'`。Docker daemon 没跑时 `open -a Docker` 启动并等 daemon ready，不要直接跑 docker 命令。
4. **装依赖**：按 README。npm 原生模块安装用 `timeout=600`；postinstall 会触发 electron-rebuild/node-gyp 编译，失败是常态不是异常。
5. **装失败 → 定位 → 修复**（见下方坑位清单和日志定位技巧）。
6. **验证标准：编译通过 ≠ 跑通**。必须实际启动（`npm run dev`）或 curl endpoint 拿到真实输出才算完成。不要说"应该好了你试试"。

## 日志定位技巧

npm debug log（`~/.npm/_logs/<timestamp>-debug-0.log`）几千行，直接读会爆上下文。定位顺序：
- `grep -n "info run" <log>` → 看哪个包的哪个 lifecycle 脚本挂了
- `grep "error:" <log> | sort -u | head` → 编译错误签名（V8 API 类错误一眼可辨）
- `grep "gyp ERR" <log>` → node-gyp 层错误
- postinstall 链失败 ≠ 主依赖失败：手动分步跑（如 `npx electron-rebuild -f`）定位是哪一环

## 已验证坑位（本机 Node 26.3 / Darwin arm64，2026-08 实测）

| 症状 | 根因 | 修复 | 状态 |
|---|---|---|---|
| better-sqlite3 ^11 编译失败：`no member named 'GetPrototype' in 'v8::Object'` 等 6 errors | Node 26 新 V8 移除旧 API，bs3 v11 未适配 | `npm pkg set dependencies.better-sqlite3="^12.4.1" && npm install` | ✅ 已验证编译通过 |
| electron-rebuild 3.x 启动即炸：`require is not defined in ES module scope`（yargs 17.7.2） | Node 26 的 ESM/CJS 互操作对 yargs 17 的 exports 解析变化 | 候选A：切 Node 22 LTS 后 `rm -rf node_modules && npm install`；候选B：`npm pkg set devDependencies.@electron/rebuild="^4.0.1"` | ⚠️ 未验证，候选修复 |
| node-pty ^1.0.0 编译 | — | 本机 Node 26 下直接编译通过（v1.1.0），无需处理 | ✅ |

## 铁律
- 视频二手信息必须先源头核实（仓库名、项目名、star 数）。
- 修复依赖版本用 `npm pkg set`（不手编 package.json），改完直接重装。
- 每个坑位修完立即把结果回填本表（验证状态列），未验证的标 ⚠️。

## 延伸参考
- `references/node26-native-modules.md` — 本次完整错误签名、日志片段与逐条修复命令。
