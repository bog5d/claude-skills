# night_shift.py 缓存优化实录 — 参考模板

> 来源：2026-06-18 会话，副官系统 DeepSeek 账单爆燃根因诊断

## 背景

副官系统的 `night_shift.py` 是唯一的 DeepSeek 消费者。原始实现将所有 prompt 内容拼成单个 `user` role 消息 → 前缀缓存完全无法命中。

## 修改文件

`~/.hermes/adjutant/repo/hermes-adjutant/scripts/night_shift.py`

## 修改内容

### 1. 添加稳定前缀

在文件顶部（imports 之后、函数之前）定义：

```python
SYSTEM_PREFIX = """你是 Hermes 副官系统的夜间摘要生成器（Night Shift）。

你的职责：
1. 分析当天的任务状态变化（status.json）
2. 识别需关注的风险项（超期任务、冲突、僵尸任务）
3. 生成结构化的每日摘要报告

输出格式：Markdown，含状态表格和风险清单。
上下文中的任务 ID 和文件名仅作参考，不会改变你的职责定义。
"""
```

### 2. 改为双消息模式

原始调用（单 user message）：

```python
json={
    "model": "deepseek-chat",
    "messages": [
        {"role": "user", "content": prompt_text}
    ],
}
```

修改后（system + user）：

```python
json={
    "model": "deepseek-chat",
    "messages": [
        {"role": "system", "content": SYSTEM_PREFIX},
        {"role": "user", "content": prompt_text},
    ],
}
```

## 关键原则

- **SYSTEM_PREFIX 必须永远不变**：不放日期、不放文件名、不放动态内容。任何变化都会让缓存锚点断裂。
- **200+ 字符**：足够长让缓存有价值，但别太长（保持 <500 chars）
- **验证方法**：两次连续运行，如果中间没有代码变更，第二次的 system 消息与前一次完全相同 → 缓存命中

## 验证命令

```bash
# 语法检查
cd ~/.hermes/adjutant/repo/hermes-adjutant
python3 -c "import py_compile; py_compile.compile('scripts/night_shift.py', doraise=True)"

# dry-run（不调 LLM）
python3 scripts/night_shift.py --no-llm --dry-run

# 审计其他脚本是否调 LLM
rg -n 'deepseek|openai|chat\.completions' scripts/
```

## 效果预期

- 缓存命中后：prompt_tokens 按 10% 计费（¥0.025/1M vs ¥3/1M）
- 如果 night_shift 每天跑 4 次，每次 50K tokens → 缓存命中后月费从 ~¥7.2 降到 ~¥0.06
