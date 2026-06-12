#!/bin/bash
#
# Hermes Gateway 监控脚本
# 功能：启动/关闭通知、异常告警、定时状态报告
# 特点：零 AI 消耗，仅使用 Telegram Bot API
#
# 放入 ~/.hermes/profiles/<profile>/bin/hermes-monitor.sh 后 chmod +x

set -euo pipefail

# ============================================================================
# 配置区 —— 必须使用绝对路径（Hermes 运行时会重写 $HOME）
# ============================================================================
PROFILES_ROOT="/Users/mac/.hermes/profiles"
MONITOR_PROFILE_DIR="${PROFILES_ROOT}/her-m2"
ENV_FILE="${MONITOR_PROFILE_DIR}/.env"
CHANNEL_FILE="${MONITOR_PROFILE_DIR}/channel_directory.json"
LOG_FILE="${MONITOR_PROFILE_DIR}/logs/monitor.log"

# 从 .env 读取 Bot Token
TELEGRAM_BOT_TOKEN=""
if [[ -f "$ENV_FILE" ]]; then
    TELEGRAM_BOT_TOKEN=$(grep "^TELEGRAM_BOT_TOKEN=" "$ENV_FILE" | cut -d= -f2 | tr -d ' ' | head -1)
fi

# 默认 Chat ID
DEFAULT_CHAT_ID="8447296166"

# 从 channel_directory.json 读取 Chat ID
CHAT_ID="$DEFAULT_CHAT_ID"
if [[ -f "$CHANNEL_FILE" ]]; then
    EXTRACTED_ID=$(grep -o '"id": "[0-9]*"' "$CHANNEL_FILE" | head -1 | grep -o '[0-9]*' || echo "")
    if [[ -n "$EXTRACTED_ID" ]]; then
        CHAT_ID="$EXTRACTED_ID"
    fi
fi

# 报告间隔（秒）- 默认4小时
REPORT_INTERVAL=${REPORT_INTERVAL:-14400}

# ============================================================================
# 日志函数
# ============================================================================
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

# ============================================================================
# Telegram 发送函数
# ============================================================================
send_telegram_message() {
    local message="$1"
    local chat_id="${2:-$CHAT_ID}"
    
    if [[ -z "$TELEGRAM_BOT_TOKEN" ]]; then
        log "ERROR" "Bot Token 未配置，无法发送消息"
        return 1
    fi
    
    local url="https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage"
    
    local retry_count=0
    local max_retries=3
    
    while [[ $retry_count -lt $max_retries ]]; do
        local response
        response=$(curl -s -X POST "$url" \
            -H "Content-Type: application/json" \
            -d "{\"chat_id\":\"$chat_id\",\"text\":\"$message\",\"parse_mode\":\"Markdown\"}" 2>&1) && break
        
        retry_count=$((retry_count + 1))
        log "WARN" "发送失败，第 $retry_count 次重试..."
        sleep 2
    done
    
    if [[ $retry_count -eq $max_retries ]]; then
        log "ERROR" "发送消息失败"
        return 1
    fi
    
    if echo "$response" | grep -q '"ok":true'; then
        log "INFO" "消息发送成功"
        return 0
    else
        log "ERROR" "API 返回错误: $response"
        return 1
    fi
}

# ============================================================================
# 获取 Gateway 状态
# ============================================================================
get_gateway_status() {
    local profiles=("default" "her-m2" "english-tutor")
    local status_info=""
    local running_count=0
    
    for profile in "${profiles[@]}"; do
        local profile_dir="${PROFILES_ROOT}/$profile"
        local pid_file="${profile_dir}/gateway.pid"
        
        local pid=""
        local state="停止"
        local uptime="N/A"
        local mem="N/A"
        
        if [[ -f "$pid_file" ]]; then
            # ⚠️ PID 文件是 JSON 格式: {"pid": 98717, "kind": "hermes-gateway", ...}
            pid=$(python3 -c "import json; print(json.load(open('$pid_file'))['pid'])" 2>/dev/null || echo "")
            if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
                state="运行中"
                running_count=$((running_count + 1))
                
                local etime=$(ps -o etime= -p "$pid" 2>/dev/null | tr -d ' ' || echo "N/A")
                uptime="$etime"
                
                local rss=$(ps -o rss= -p "$pid" 2>/dev/null | tr -d ' ' || echo "0")
                if [[ "$rss" =~ ^[0-9]+$ ]]; then
                    mem="$((rss / 1024))MB"
                fi
            else
                state="异常(僵尸PID)"
            fi
        fi
        
        status_info+="\n• $profile: $state"
        if [[ -n "$pid" ]]; then
            status_info+=" (PID:$pid)"
        fi
        if [[ "$state" == "运行中" ]]; then
            status_info+=" | 运行:$uptime | 内存:$mem"
        fi
    done
    
    # ⚠️ 不要用 `return $running_count`（set -e 下非零值会导致退出）
    echo -e "$status_info"
    echo "$running_count"
}

# ============================================================================
# 获取 REST API Gateway 状态
# ============================================================================
get_rest_gateway_status() {
    if curl -s http://localhost:18765/health >/dev/null 2>&1; then
        echo "运行中"
    else
        echo "未运行"
    fi
}

# ============================================================================
# 获取系统状态
# ============================================================================
get_system_status() {
    local load=$(uptime | awk -F'load averages:' '{print $2}' | awk '{print $1}' | tr -d ',')
    local mem_info=$(vm_stat 2>/dev/null | awk '
        /Pages free/ { free = $3 }
        /Pages active/ { active = $3 }
        /Pages inactive/ { inactive = $3 }
        /Pages wired/ { wired = $3 }
        END {
            total = (free + active + inactive + wired) * 4096 / 1024 / 1024 / 1024
            used = (active + inactive + wired) * 4096 / 1024 / 1024 / 1024
            printf "%.1fGB/%.1fGB", used, total
        }
    ' || echo "N/A")
    
    echo "负载: $load | 内存: $mem_info"
}

# ============================================================================
# 生成完整状态报告
# ============================================================================
generate_full_report() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local hostname=$(hostname -s)
    
    local gateway_info
    gateway_info=$(get_gateway_status)
    # ⚠️ macOS 不支持 head -n -1，用 sed '$d' 删除最后一行（running_count）
    local gateway_status
    gateway_status=$(echo "$gateway_info" | sed '$d')
    local running_count
    running_count=$(echo "$gateway_info" | tail -n 1)
    
    local rest_status=$(get_rest_gateway_status)
    local system_status=$(get_system_status)
    
    cat <<EOF
📊 *Hermes 系统状态报告*
━━━━━━━━━━━━━━━━━━━━━
🕐 时间: $timestamp
💻 主机: $hostname

🚀 Gateway 状态 ($running_count/3 运行中):
$gateway_status

🔌 REST API Gateway (18765):
• 状态: $rest_status

💾 系统状态:
• $system_status
━━━━━━━━━━━━━━━━━━━━━
EOF
}

# ============================================================================
# 命令处理
# ============================================================================
case "${1:-status}" in
    "startup")
        local profile="${2:-unknown}"
        local pid="${3:-$$}"
        local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        
        message="✅ *Gateway 已启动*
━━━━━━━━━━━━━━━━━━━━━
🚀 Profile: \`$profile\`
🆔 PID: \`$pid\`
🕐 时间: $timestamp
━━━━━━━━━━━━━━━━━━━━━"
        
        send_telegram_message "$message"
        log "INFO" "发送启动通知: profile=$profile, pid=$pid"
        ;;
    
    "shutdown")
        local profile="${2:-unknown}"
        local delay="${3:-30}"
        local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        
        message="⚠️ *Gateway 即将关闭*
━━━━━━━━━━━━━━━━━━━━━
🛑 Profile: \`$profile\`
⏱️ 预计关闭时间: ${delay}秒后
🕐 时间: $timestamp
━━━━━━━━━━━━━━━━━━━━━"
        
        send_telegram_message "$message"
        log "INFO" "发送关闭预告: profile=$profile, delay=${delay}s"
        ;;
    
    "crash")
        local profile="${2:-unknown}"
        local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        
        message="🚨 *Gateway 异常崩溃*
━━━━━━━━━━━━━━━━━━━━━
💥 Profile: \`$profile\`
🕐 时间: $timestamp
⚡ 建议立即检查日志
━━━━━━━━━━━━━━━━━━━━━"
        
        send_telegram_message "$message"
        log "ERROR" "发送崩溃告警: profile=$profile"
        ;;
    
    "report")
        local report=$(generate_full_report)
        send_telegram_message "$report"
        log "INFO" "发送定时状态报告"
        ;;
    
    "status")
        generate_full_report
        ;;
    
    "watch")
        log "INFO" "启动监控模式，检查间隔: ${REPORT_INTERVAL}秒"
        
        local last_running_count=-1
        
        while true; do
            local gw_info
            gw_info=$(get_gateway_status)
            local running_count
            running_count=$(echo "$gw_info" | tail -n 1)
            
            if [[ $last_running_count -ne -1 && $last_running_count -ne $running_count ]]; then
                log "WARN" "Gateway 数量变化: $last_running_count -> $running_count"
                if [[ $running_count -lt $last_running_count ]]; then
                    send_telegram_message "🚨 *Gateway 异常*
检测到 Gateway 数量减少！
当前运行: $running_count/3"
                fi
            fi
            
            last_running_count=$running_count
            sleep "$REPORT_INTERVAL"
        done
        ;;
    
    *)
        echo "用法: $0 {startup|shutdown|crash|report|status|watch} [profile] [delay/pid]"
        exit 1
        ;;
esac
