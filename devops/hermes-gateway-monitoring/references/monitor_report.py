#!/usr/bin/env python3
"""
Hermes Monitor Report Generator v2
Called by hermes-monitor.sh to generate the status report.
Outputs formatted markdown to stdout.
"""
import json, os, subprocess, yaml, urllib.request, ssl, time
from datetime import datetime, timedelta

PROFILES_ROOT = "/Users/mac/.hermes/profiles"
HERMES_HOME = "/Users/mac/.hermes"

PROFILES = {
    "default":  {"home": HERMES_HOME, "config": f"{HERMES_HOME}/config.yaml", "pid_file": f"{HERMES_HOME}/gateway.pid"},
    "her-m2":   {"home": f"{PROFILES_ROOT}/her-m2", "config": f"{PROFILES_ROOT}/her-m2/config.yaml", "pid_file": f"{PROFILES_ROOT}/her-m2/gateway.pid"},
    "english-tutor": {"home": f"{PROFILES_ROOT}/english-tutor", "config": f"{PROFILES_ROOT}/english-tutor/config.yaml", "pid_file": f"{PROFILES_ROOT}/english-tutor/gateway.pid"},
}


def get_model_info(profile):
    cfg = PROFILES[profile]["config"]
    if not os.path.exists(cfg):
        return "N/A"
    try:
        c = yaml.safe_load(open(cfg))
    except Exception:
        return "解析失败"
    m = c.get("model", {})
    main = f"{m.get('default','?')} @ {m.get('provider','?')}"
    fb = c.get("fallback_providers", [])
    if fb:
        fbs = " | ".join(f"{f['model']} @ {f['provider']}" for f in fb)
        main += f"  (↳ {fbs})"
    return main


def get_gateway_status(profile):
    """Returns (is_running, pid, state, uptime, mem_mb)"""
    pid_file = PROFILES[profile]["pid_file"]
    if not os.path.exists(pid_file):
        return False, None, "停止", "N/A", "N/A"
    try:
        data = json.load(open(pid_file))
        pid = data.get("pid")
    except Exception:
        return False, None, "异常", "N/A", "N/A"

    if not pid:
        return False, None, "异常", "N/A", "N/A"

    # Check if process is alive
    try:
        os.kill(pid, 0)
    except (OSError, ProcessLookupError):
        return False, pid, "异常(僵尸PID)", "N/A", "N/A"

    # Get uptime and memory
    uptime = "N/A"
    mem = "N/A"
    try:
        result = subprocess.run(["ps", "-o", "etime=,rss=", "-p", str(pid)],
                                capture_output=True, text=True, timeout=3)
        if result.returncode == 0:
            parts = result.stdout.strip().split()
            if len(parts) >= 1:
                uptime = parts[0].strip()
            if len(parts) >= 2:
                rss = int(parts[1])
                mem = f"{rss // 1024}MB"
    except Exception:
        pass

    return True, pid, "运行中", uptime, mem


def get_session_count(profile):
    sess_dir = os.path.join(PROFILES[profile]["home"], "sessions")
    if not os.path.exists(sess_dir):
        return 0
    return len([f for f in os.listdir(sess_dir) if f.endswith(".json")])


def get_disk_usage(profile):
    home = PROFILES[profile]["home"]
    sizes = {}
    for sub in ["logs", "sessions"]:
        d = os.path.join(home, sub)
        if os.path.exists(d):
            try:
                result = subprocess.run(["du", "-sh", d], capture_output=True, text=True, timeout=5)
                sizes[sub] = result.stdout.split()[0] if result.returncode == 0 else "?"
            except Exception:
                sizes[sub] = "?"
        else:
            sizes[sub] = "0"
    return sizes


def get_error_summary(profile):
    error_log = os.path.join(PROFILES[profile]["home"], "logs", "gateway.error.log")
    if not os.path.exists(error_log):
        return {"total": 0, "api": 0, "conn": 0, "tool": 0, "infra": 0, "timeout": 0, "other": 0}

    cutoff = datetime.now() - timedelta(hours=1)
    cutoff_str = cutoff.strftime("%Y-%m-%d %H:%M")

    total = 0
    api_err = 0    # 429/401/402/403/rate limits
    conn_err = 0   # telegram timeout, websocket drops
    tool_err = 0   # tool_executor failures
    infra_err = 0  # port conflicts, system errors
    timeout_err = 0  # agent idle timeouts
    other_err = 0

    try:
        with open(error_log) as f:
            for line in f:
                ts_str = line[:19]
                if ts_str < cutoff_str:
                    continue
                if "ERROR" not in line and "CRITICAL" not in line:
                    continue
                total += 1
                if any(kw in line for kw in ["429", "401", "402", "403", "rate.limit", "RateLimit",
                                                 "Insufficient Balance"]):
                    api_err += 1
                elif any(kw in line for kw in ["connect timed out", "Server disconnected", "RemoteProtocolError",
                                                 "telegram error", "poll error", "receive message loop exit",
                                                 "no close frame", "Network is unreachable", "Connection refused",
                                                 "Network Retry Loop", "Fatal telegram", "get_updates"]):
                    conn_err += 1
                elif "tool_executor" in line:
                    tool_err += 1
                elif any(kw in line for kw in ["already in use", "Failed to start API"]):
                    infra_err += 1
                elif any(kw in line for kw in ["Agent idle", "idle.*timeout"]):
                    timeout_err += 1
                elif "vision_tools" in line or "Error analyzing image" in line:
                    tool_err += 1
                elif "Non-retryable client error" in line:
                    api_err += 1
    except Exception:
        pass

    other = total - api_err - conn_err - tool_err - infra_err - timeout_err
    if other < 0:
        other = 0

    return {"total": total, "api": api_err, "conn": conn_err, "tool": tool_err, 
            "infra": infra_err, "timeout": timeout_err, "other": other}


def check_providers():
    """Returns list of (name, status) tuples"""
    results = []
    ctx = ssl.create_default_context()
    auth_file = os.path.join(HERMES_HOME, "auth.json")
    try:
        auth = json.load(open(auth_file))
        for pool_name, creds in auth.get("credential_pool", {}).items():
            if not creds:
                continue
            token = creds[0].get("access_token", "")
            url = creds[0].get("base_url", "").split("#")[0].strip() + "/models"
            try:
                req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
                resp = urllib.request.urlopen(req, timeout=5, context=ctx)
                status = "OK" if resp.status == 200 else str(resp.status)
            except Exception as e:
                status = f"FAIL({str(e)[:40]})"
            results.append((pool_name, status))
    except Exception as e:
        results.append(("ERROR", str(e)[:60]))
    return results


def check_rest_api():
    try:
        req = urllib.request.Request("http://localhost:18765/health")
        urllib.request.urlopen(req, timeout=2, context=ssl.create_default_context())
        return True
    except Exception:
        return False


def get_system_info():
    # CPU load
    try:
        result = subprocess.run(["uptime"], capture_output=True, text=True)
        load = result.stdout.split("load averages:")[-1].strip().split()[0].rstrip(",")
    except Exception:
        load = "N/A"

    # Memory
    try:
        result = subprocess.run(["vm_stat"], capture_output=True, text=True)
        pages = {}
        for line in result.stdout.splitlines():
            if ":" in line:
                key, val = line.split(":", 1)
                key = key.strip().strip('"')
                try:
                    pages[key] = int(val.strip().rstrip("."))
                except ValueError:
                    pass
        free = pages.get("Pages free", 0)
        active = pages.get("Pages active", 0)
        inactive = pages.get("Pages inactive", 0)
        wired = pages.get("Pages wired down", 0)
        total_gb = (free + active + inactive + wired) * 4096 / 1024 / 1024 / 1024
        used_gb = (active + inactive + wired) * 4096 / 1024 / 1024 / 1024
        pct = int(used_gb / total_gb * 100) if total_gb > 0 else 0
        mem_str = f"{used_gb:.1f}GB/{total_gb:.1f}GB ({pct}%)"
    except Exception:
        mem_str = "N/A"

    # Hermes disk
    try:
        result = subprocess.run(["du", "-sh", HERMES_HOME], capture_output=True, text=True, timeout=5)
        disk = result.stdout.split()[0]
    except Exception:
        disk = "N/A"

    return load, mem_str, disk


def generate_report():
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    hostname = os.uname().nodename.split(".")[0]

    lines = []
    lines.append("📊 *Hermes 系统状态报告*")
    lines.append("━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"🕐 {ts}")
    lines.append(f"💻 {hostname}")
    lines.append("")

    # --- Gateways ---
    running = 0
    gw_lines = []
    gw_lines.append("🚀 *Gateway 状态*")
    gw_lines.append("━━━━━━━━━━━━━━━━━━━━━")

    for profile in ["default", "her-m2", "english-tutor"]:
        alive, pid, state, uptime, mem = get_gateway_status(profile)
        model = get_model_info(profile)
        sessions = get_session_count(profile)
        disk = get_disk_usage(profile)
        errors = get_error_summary(profile)

        emoji = "🟢" if alive else ("🟡" if pid else "🔴")
        if alive:
            running += 1

        block = f"*{emoji} {profile}* — {state}\n"
        block += f"  PID: `{pid or 'N/A'}` | 运行: {uptime} | 内存: {mem}\n"
        block += f"  🧠 {model}\n"
        block += f"  📊 会话: {sessions} | 磁盘: logs={disk.get('logs','?')} sessions={disk.get('sessions','?')}\n"

        if errors["total"] > 0:
            parts = []
            if errors["api"]: parts.append(f"API:{errors['api']}")
            if errors["conn"]: parts.append(f"连接:{errors['conn']}")
            if errors["tool"]: parts.append(f"工具:{errors['tool']}")
            if errors["timeout"]: parts.append(f"超时:{errors['timeout']}")
            if errors["infra"]: parts.append(f"基础设施:{errors['infra']}")
            if errors["other"]: parts.append(f"其他:{errors['other']}")
            block += f"  ⚠️ 最近1h错误: {' '.join(parts)}\n"

        gw_lines.append(block)

    gw_lines.insert(1, f"*Gateway ({running}/3)*")
    lines.extend(gw_lines)
    lines.append("")

    # --- Providers ---
    lines.append("🌐 *Provider 连通性*")
    for name, status in check_providers():
        emoji = "✅" if status == "OK" else "❌"
        lines.append(f"  {emoji} {name}: {status}")
    lines.append("")

    # --- REST API ---
    rest_ok = check_rest_api()
    lines.append(f"🔌 *REST API* (18765): {'🟢 运行中' if rest_ok else '⚫ 未运行'}")
    lines.append("")

    # --- System ---
    load, mem_str, disk = get_system_info()
    lines.append("💾 *系统资源*")
    lines.append(f"  CPU 负载: {load}")
    lines.append(f"  内存: {mem_str}")
    lines.append(f"  Hermes 磁盘: {disk}")
    lines.append("━━━━━━━━━━━━━━━━━━━━━")

    return "\n".join(lines)


if __name__ == "__main__":
    print(generate_report())
