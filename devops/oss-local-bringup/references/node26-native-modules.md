# Node 26 原生模块编译坑位实录（2026-08-30, munder-difflin bringup）

环境：Node v26.3.0 / npm 11.16.0 / Darwin arm64 / Xcode CLT 已装。

## 坑 1：better-sqlite3 ^11 编译失败

错误签名（node-gyp rebuild 阶段，6 errors）：
```
./src/util/binder.lzz:40:37: error: no member named 'GetPrototype' in 'v8::Object'; did you mean 'GetPrototypeV2'?
./src/better_sqlite3.lzz:68:34: error: no member named 'GetIsolate' in 'v8::Context'
./src/objects/database.lzz:416:89: error: no member named 'This' in 'v8::PropertyCallbackInfo<v8::Value>'
```
根因：Node 26 的 V8 移除/改名了旧 API，better-sqlite3 v11 未适配。

修复（已验证编译通过）：
```bash
npm pkg set dependencies.better-sqlite3="^12.4.1"
npm install   # v12.11.1 编译通过
```

## 坑 2：electron-rebuild 3.x 在 Node 26 下启动即炸

错误签名：
```
ReferenceError: require is not defined in ES module scope, you can use import instead
    at file:///...node_modules/yargs/yargs:3:69
```
根因：yargs 17.7.2 的 `yargs` 入口文件是 ESM wrapper 里面调 require，Node 26 对 exports 解析的互操作行为变化导致直接炸。electron-rebuild 3.7.2 通过 yargs 解析参数，连带挂掉。

候选修复（本轮未验证完，下轮二选一先试 A）：
- A. 切 Node 22 LTS：`nvm install 22 && nvm use 22 && rm -rf node_modules && npm install`
- B. 升级 electron-rebuild：`npm pkg set devDependencies.@electron/rebuild="^4.0.1" && npm install`

## 坑 3：node-pty ^1.0.0

Node 26 下解析到 v1.1.0，install + postinstall 全部 code 0 直接通过，无需处理。

## npm debug log 定位套路

日志在 `~/.npm/_logs/<timestamp>-debug-0.log`（几千行）：
- `grep -n "info run" <log>` → 哪个包哪个 lifecycle 挂了（带退出码）
- `grep "error:" <log> | sort -u | head` → 编译错误签名去重
- postinstall 链失败 ≠ 主依赖失败：手动分步跑 `npx electron-rebuild -f` 定位具体环节

## 教训
- 老项目（package.json 停更于 Node 18/20 时代）+ 本机 Node 26 = 原生模块连环坑。先看 package.json 里原生依赖版本，预判兼容性，别等编译炸了再查。
- 修复依赖版本用 `npm pkg set`，不手编 package.json。
