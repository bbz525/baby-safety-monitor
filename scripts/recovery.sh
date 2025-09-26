#!/bin/bash

# 故障恢复和自愈脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_DIR/logs/recovery.log"

# 服务配置
SERVICES=("backend-go" "frontend" "vision" "agent")
SERVICE_URLS=(
    "http://localhost:8080/health"
    "http://localhost:5173"
    "http://localhost:8001/health"
    "http://localhost:8002/health"
)

# 恢复策略配置
MAX_RESTART_ATTEMPTS=3
HEALTH_CHECK_TIMEOUT=10
RESTART_COOLDOWN=30
NOTIFICATION_ENABLED=true

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo -e "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

log_info() {
    log "INFO" "${BLUE}$@${NC}"
}

log_success() {
    log "SUCCESS" "${GREEN}$@${NC}"
}

log_warning() {
    log "WARNING" "${YELLOW}$@${NC}"
}

log_error() {
    log "ERROR" "${RED}$@${NC}"
}

# 初始化日志目录
mkdir -p "$(dirname "$LOG_FILE")"

# 检查服务健康状态
check_service_health() {
    local service_name=$1
    local url=$2
    local timeout=${3:-$HEALTH_CHECK_TIMEOUT}
    
    if curl -s --max-time "$timeout" "$url" > /dev/null 2>&1; then
        return 0  # 健康
    else
        return 1  # 不健康
    fi
}

# 检查Docker容器状态
check_container_status() {
    local service_name=$1
    
    local container_name="baby-safety-monitor-${service_name}-1"
    
    if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "$container_name.*Up"; then
        return 0  # 运行中
    else
        return 1  # 未运行
    fi
}

# 重启服务
restart_service() {
    local service_name=$1
    local attempt=${2:-1}
    
    log_info "尝试重启服务: $service_name (第 $attempt 次尝试)"
    
    # 使用Docker Compose重启服务
    if docker-compose -f "$PROJECT_DIR/docker-compose.yml" restart "$service_name"; then
        log_success "服务 $service_name 重启成功"
        
        # 等待服务启动
        sleep 10
        
        return 0
    else
        log_error "服务 $service_name 重启失败"
        return 1
    fi
}

# 强制重建服务
rebuild_service() {
    local service_name=$1
    
    log_warning "强制重建服务: $service_name"
    
    # 停止并删除容器
    docker-compose -f "$PROJECT_DIR/docker-compose.yml" stop "$service_name"
    docker-compose -f "$PROJECT_DIR/docker-compose.yml" rm -f "$service_name"
    
    # 重新构建和启动
    if docker-compose -f "$PROJECT_DIR/docker-compose.yml" up -d --build "$service_name"; then
        log_success "服务 $service_name 重建成功"
        
        # 等待服务启动
        sleep 30
        
        return 0
    else
        log_error "服务 $service_name 重建失败"
        return 1
    fi
}

# 检查系统资源
check_system_resources() {
    log_info "检查系统资源..."
    
    # 检查磁盘空间
    local disk_usage=$(df -h "$PROJECT_DIR" | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$disk_usage" -gt 90 ]; then
        log_warning "磁盘使用率过高: ${disk_usage}%"
        
        # 清理旧日志
        find "$PROJECT_DIR/logs" -name "*.log.*" -mtime +7 -delete 2>/dev/null || true
        log_info "已清理旧日志文件"
        
        return 1
    fi
    
    # 检查内存使用
    local memory_usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}' 2>/dev/null || echo "0")
    if [ "$memory_usage" -gt 90 ]; then
        log_warning "内存使用率过高: ${memory_usage}%"
        
        # 清理Docker无用镜像和容器
        docker system prune -f > /dev/null 2>&1 || true
        log_info "已清理Docker无用资源"
        
        return 1
    fi
    
    return 0
}

# 修复网络问题
fix_network_issues() {
    log_info "检查和修复网络问题..."
    
    # 重创建Docker网络
    local network_name="baby-safety-monitor_baby-safety-net"
    
    if docker network ls | grep -q "$network_name"; then
        log_info "重建Docker网络"
        docker-compose -f "$PROJECT_DIR/docker-compose.yml" down
        docker network rm "$network_name" 2>/dev/null || true
        docker-compose -f "$PROJECT_DIR/docker-compose.yml" up -d
    fi
}

# 修复数据库问题
fix_database_issues() {
    local db_file="$PROJECT_DIR/data/baby_safety.db"
    
    log_info "检查数据库完整性..."
    
    if [ ! -f "$db_file" ]; then
        log_warning "数据库文件不存在，将在服务启动时重新创建"
        return 0
    fi
    
    # 检查数据库文件完整性
    if ! sqlite3 "$db_file" "PRAGMA integrity_check;" > /dev/null 2>&1; then
        log_error "数据库文件损坏"
        
        # 备份损坏的数据库
        local backup_name="baby_safety_corrupted_$(date +%Y%m%d_%H%M%S).db"
        cp "$db_file" "$PROJECT_DIR/data/$backup_name"
        log_info "已备份损坏的数据库: $backup_name"
        
        # 删除损坏的数据库（服务会重新创建）
        rm "$db_file"
        log_info "已删除损坏的数据库文件，服务将重新创建"
        
        return 1
    fi
    
    return 0
}

# 发送通知
send_notification() {
    local title=$1
    local message=$2
    local level=${3:-"info"}
    
    if [ "$NOTIFICATION_ENABLED" != "true" ]; then
        return
    fi
    
    # 发送钉钉通知
    if [ -n "${DINGTALK_WEBHOOK:-}" ]; then
        local color="#00ff00"  # 绿色
        case "$level" in
            "warning") color="#ffff00" ;;  # 黄色
            "error") color="#ff0000" ;;    # 红色
        esac
        
        local payload=$(cat << EOF
{
    "msgtype": "markdown",
    "markdown": {
        "title": "$title",
        "text": "### $title\n\n$message\n\n> 时间: $(date '+%Y-%m-%d %H:%M:%S')\n> 主机: $(hostname)"
    }
}
EOF
        )
        
        curl -X POST "$DINGTALK_WEBHOOK" \
            -H "Content-Type: application/json" \
            -d "$payload" > /dev/null 2>&1 || true
    fi
    
    # 记录到系统日志
    logger -t "baby-safety-recovery" "$title: $message"
}

# 执行恢复策略
execute_recovery() {
    local service_name=$1
    local service_url=$2
    
    log_info "开始恢复服务: $service_name"
    
    local attempt=1
    while [ $attempt -le $MAX_RESTART_ATTEMPTS ]; do
        log_info "恢复尝试 $attempt/$MAX_RESTART_ATTEMPTS"
        
        # 检查容器状态
        if ! check_container_status "$service_name"; then
            log_warning "容器未运行，尝试启动"
            docker-compose -f "$PROJECT_DIR/docker-compose.yml" up -d "$service_name"
            sleep 15
        fi
        
        # 尝试重启服务
        if restart_service "$service_name" "$attempt"; then
            # 等待一段时间后检查健康状态
            sleep 30
            
            if check_service_health "$service_name" "$service_url"; then
                log_success "服务 $service_name 恢复成功"
                send_notification "服务恢复成功" "服务 $service_name 已成功恢复" "info"
                return 0
            fi
        fi
        
        # 如果是最后一次尝试，进行强制重建
        if [ $attempt -eq $MAX_RESTART_ATTEMPTS ]; then
            log_warning "常规重启失败，尝试重建服务"
            
            if rebuild_service "$service_name"; then
                sleep 30
                if check_service_health "$service_name" "$service_url"; then
                    log_success "服务 $service_name 重建后恢复成功"
                    send_notification "服务重建成功" "服务 $service_name 重建后恢复成功" "warning"
                    return 0
                fi
            fi
        fi
        
        attempt=$((attempt + 1))
        
        if [ $attempt -le $MAX_RESTART_ATTEMPTS ]; then
            log_info "等待 $RESTART_COOLDOWN 秒后重试..."
            sleep $RESTART_COOLDOWN
        fi
    done
    
    log_error "服务 $service_name 恢复失败"
    send_notification "服务恢复失败" "服务 $service_name 在 $MAX_RESTART_ATTEMPTS 次尝试后仍然无法恢复" "error"
    return 1
}

# 主健康检查和恢复循环
main_recovery_loop() {
    log_info "启动故障恢复监控..."
    
    while true; do
        local failed_services=()
        
        # 检查系统资源
        if ! check_system_resources; then
            log_warning "系统资源不足，可能影响服务运行"
        fi
        
        # 检查每个服务
        for i in "${!SERVICES[@]}"; do
            local service="${SERVICES[$i]}"
            local url="${SERVICE_URLS[$i]}"
            
            if ! check_service_health "$service" "$url"; then
                log_warning "检测到服务故障: $service"
                failed_services+=("$service:$url")
            fi
        done
        
        # 恢复故障服务
        if [ ${#failed_services[@]} -gt 0 ]; then
            log_warning "发现 ${#failed_services[@]} 个故障服务，开始恢复..."
            
            for service_info in "${failed_services[@]}"; do
                local service_name=$(echo "$service_info" | cut -d: -f1)
                local service_url=$(echo "$service_info" | cut -d: -f2-)
                
                execute_recovery "$service_name" "$service_url"
            done
            
            # 如果有多个服务故障，可能是系统性问题
            if [ ${#failed_services[@]} -gt 2 ]; then
                log_warning "多个服务同时故障，检查系统问题..."
                
                fix_network_issues
                fix_database_issues
                
                # 重启所有服务
                log_info "重启所有服务..."
                docker-compose -f "$PROJECT_DIR/docker-compose.yml" restart
                sleep 60
            fi
        else
            log_info "所有服务运行正常"
        fi
        
        # 等待下次检查
        sleep 60
    done
}

# 一次性健康检查
run_health_check() {
    log_info "执行一次性健康检查..."
    
    local all_healthy=true
    
    for i in "${!SERVICES[@]}"; do
        local service="${SERVICES[$i]}"
        local url="${SERVICE_URLS[$i]}"
        
        if check_service_health "$service" "$url"; then
            log_success "✅ $service: 健康"
        else
            log_error "❌ $service: 故障"
            all_healthy=false
        fi
    done
    
    if $all_healthy; then
        log_success "所有服务运行正常"
        return 0
    else
        log_error "发现服务故障"
        return 1
    fi
}

# 手动恢复特定服务
manual_recovery() {
    local service_name=$1
    
    if [ -z "$service_name" ]; then
        log_error "请指定要恢复的服务名称"
        echo "可用服务: ${SERVICES[*]}"
        exit 1
    fi
    
    # 查找服务URL
    local service_url=""
    for i in "${!SERVICES[@]}"; do
        if [ "${SERVICES[$i]}" = "$service_name" ]; then
            service_url="${SERVICE_URLS[$i]}"
            break
        fi
    done
    
    if [ -z "$service_url" ]; then
        log_error "未知的服务名称: $service_name"
        echo "可用服务: ${SERVICES[*]}"
        exit 1
    fi
    
    execute_recovery "$service_name" "$service_url"
}

# 主函数
main() {
    case "${1:-monitor}" in
        "monitor")
            main_recovery_loop
            ;;
        "check")
            run_health_check
            ;;
        "recover")
            manual_recovery "$2"
            ;;
        "fix-network")
            fix_network_issues
            ;;
        "fix-database")
            fix_database_issues
            ;;
        "help"|*)
            echo "婴儿安全监控系统故障恢复工具"
            echo ""
            echo "用法: $0 <command> [options]"
            echo ""
            echo "命令:"
            echo "  monitor           启动持续监控和自动恢复 (默认)"
            echo "  check             执行一次性健康检查"
            echo "  recover <service> 手动恢复指定服务"
            echo "  fix-network       修复网络问题"
            echo "  fix-database      修复数据库问题"
            echo "  help              显示此帮助信息"
            echo ""
            echo "可用服务: ${SERVICES[*]}"
            ;;
    esac
}

# 信号处理
trap 'log_info "收到退出信号，停止监控..."; exit 0' SIGINT SIGTERM

# 执行主函数
main "$@"