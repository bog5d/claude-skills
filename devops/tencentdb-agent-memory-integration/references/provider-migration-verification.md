# Provider 迁移验证清单

## 适用场景

批量将多个 Hermes profile 的某个辅助 provider（如 `web_extract`）从 A 切换到 B。

## 验证步骤

### 1. 全量扫描 —— 确认没有遗漏

```bash
search_files pattern="web_extract" file_glob="config.yaml" path="~/.hermes"
```

### 2. 逐个读取 web_extract 段 —— 确认值正确

```bash
for cfg in ~/.hermes/config.yaml ~/.hermes/profiles/*/config.yaml; do
  echo "=== $cfg ==="
  python3 -c "
import yaml
with open('$cfg') as f:
    c = yaml.safe_load(f)
we = c.get('auxiliary', {}).get('web_extract', {})
print(f'  provider: {we.get(\"provider\", \"NOT SET\")}')
print(f'  model: {we.get(\"model\", \"NOT SET\")}')
"
done
```

### 3. 查重复 key（YAML 允许但语义模糊）

```bash
# 查找每个 yaml 文件中 web_extract 段是否有重复 key
python3 -c "
import yaml, glob, re
for path in glob.glob('/Users/mac/.hermes/profiles/*/config.yaml') + ['/Users/mac/.hermes/config.yaml']:
    with open(path) as f:
        text = f.read()
    # 找 web_extract 段
    m = re.search(r'web_extract:(.*?)(?=\n\S)', text, re.DOTALL)
    if m:
        keys = re.findall(r'^\s{2,}(\w+):', m.group(1), re.MULTILINE)
        dupes = [k for k in set(keys) if keys.count(k) > 1]
        if dupes:
            print(f'WARN: {path} has duplicate keys in web_extract: {dupes}')
"
```

## 常见陷阱

### YAML 重复 key — 最后一个胜出，但旧值残留

**症状**：patch 追加了新配置行，但没有删除旧行。结果：
```yaml
web_extract:
  model: deepseek-chat      # ← 旧值（残留）
  provider: agnes
  model: agnes-2.0-flash    # ← 新值（YAML 取最后一个）
```

虽然运行时行为正确（`agnes-2.0-flash` 生效），但残留的旧值会误导后续维护者。

**修复**：合并 web_extract 段，删除所有重复 key 的旧值条目。

### 不同 profile 的 web_extract 字段顺序可能不同

如 `finance` profile 的 `web_extract` 段包含 `api_key` 和 `base_url`，而 `default` 没有。逐 profile 读取确认，不要假设统一格式。
