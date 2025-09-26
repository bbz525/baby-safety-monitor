#!/bin/bash

# 性能监控和健康检查脚本

set -e

BASE_URL=${BASE_URL:-"http://localhost:8080"}
VISION_URL=${VISION_URL:-"http://localhost:8001"}
AGENT_URL=${AGENT_URL:-"http://localhost:8002"}
FRONTEND_URL=${FRONTEND_URL:-"http://localhost:5173"}

REPORT_DIR="./monitoring/reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="$REPORT_DIR/health_report_$TIMESTAMP.json"

# 创建报告目录
mkdir -p $REPORT_DIR

echo "🔍 开始系统健康检查..."

# 检查服务健康状态
check_service_health() {
    local service_name=$1
    local url=$2
    local timeout=${3:-10}
    
    echo "🏥 检查 $service_name 健康状态..."
    
    start_time=$(date +%s%3N)
    
    if response=$(curl -s -w "HTTPSTATUS:%{http_code};TIME:%{time_total}" --max-time $timeout "$url/health" 2>/dev/null); then
        http_code=$(echo "$response" | sed -E 's/.*HTTPSTATUS:([0-9]{3}).*/\1/')
        response_time=$(echo "$response" | sed -E 's/.*TIME:([0-9.]+).*/\1/')
        body=$(echo "$response" | sed -E 's/HTTPSTATUS:[0-9]{3};TIME:[0-9.]+//')
        
        if [ "$http_code" = "200" ]; then
            status="healthy"
            echo "✅ $service_name: 健康 (${response_time}s)"
        else
            status="unhealthy"
            echo "❌ $service_name: 不健康 (HTTP $http_code)"
        fi
    else
        status="unreachable"
        response_time="timeout"
        body=""
        echo "💥 $service_name: 无法访问"
    fi
    
    # 返回JSON格式的结果
    cat << EOF
{
    "service": "$service_name",
    "url": "$url",
    "status": "$status",
    "http_code": "$http_code",
    "response_time": "$response_time",
    "timestamp": "$(date -Iseconds)",
    "body": $(echo "$body" | jq -R . 2>/dev/null || echo '""')
}
EOF
}

# 检查API性能
check_api_performance() {
    local service_name=$1
    local base_url=$2
    
    echo "⚡ 检查 $service_name API性能..."
    
    # 测试关键API端点
    endpoints=(
        "GET:/health"
        "GET:/metrics"
    )
    
    if [ "$service_name" = "Backend" ]; then
        endpoints+=(
            "GET:/api/events/recent?minutes=5"
            "GET:/api/alerts/recent?minutes=5"
            "GET:/api/zones"
        )
    elif [ "$service_name" = "Vision" ]; then
        endpoints+=(
            "GET:/cameras"
            "GET:/last.jpg"
        )
    fi
    
    local results=[]
    
    for endpoint in "${endpoints[@]}"; do
        method=$(echo "$endpoint" | cut -d':' -f1)
        path=$(echo "$endpoint" | cut -d':' -f2)
        url="$base_url$path"
        
        echo "📊 测试 $method $path..."
        
        # 使用curl测试性能
        if result=$(curl -s -w "@-" --max-time 10 -X "$method" "$url" << 'EOF'
{
    "time_total": %{time_total},
    "time_connect": %{time_connect},
    "time_starttransfer": %{time_starttransfer},
    "size_download": %{size_download},
    "speed_download": %{speed_download},
    "http_code": %{http_code}
}
EOF
        ); then
            echo "  ✅ $path: $(echo "$result" | jq -r '.time_total')s"
        else
            echo "  ❌ $path: 失败"
            result='{"error": "failed", "http_code": 0}'
        fi
        
        # 添加到结果数组
        endpoint_result=$(cat << EOF
{
    "endpoint": "$path",
    "method": "$method",
    "url": "$url",
    "timestamp": "$(date -Iseconds)",
    "metrics": $result
}
EOF
        )
        
        results=$(echo "$results" | jq ". + [$endpoint_result]" 2>/dev/null || echo "[$endpoint_result]")
    done
    
    echo "$results"
}

# 检查系统资源
check_system_resources() {
    echo "💻 检查系统资源..."
    
    # CPU使用率
    cpu_usage=$(top -l 1 | grep "CPU usage" | awk '{print $3}' | sed 's/%//' || echo "0")
    
    # 内存使用率
    memory_info=$(vm_stat)
    page_size=$(vm_stat | grep "page size" | awk '{print $8}' || echo "4096")
    free_pages=$(echo "$memory_info" | grep "Pages free" | awk '{print $3}' | sed 's/\.//')
    active_pages=$(echo "$memory_info" | grep "Pages active" | awk '{print $3}' | sed 's/\.//')
    inactive_pages=$(echo "$memory_info" | grep "Pages inactive" | awk '{print $3}' | sed 's/\.//')
    wired_pages=$(echo "$memory_info" | grep "Pages wired down" | awk '{print $4}' | sed 's/\.//')
    
    total_pages=$((free_pages + active_pages + inactive_pages + wired_pages))
    used_pages=$((total_pages - free_pages))
    memory_usage=$((used_pages * 100 / total_pages))
    
    # 磁盘使用率
    disk_usage=$(df -h . | awk 'NR==2 {print $5}' | sed 's/%//')
    
    # Docker容器状态
    docker_status=$(docker ps --format "table {{.Names}}\t{{.Status}}" 2>/dev/null || echo "Docker not available")
    
    cat << EOF
{
    "timestamp": "$(date -Iseconds)",
    "cpu_usage_percent": $cpu_usage,
    "memory_usage_percent": $memory_usage,
    "disk_usage_percent": $disk_usage,
    "docker_containers": $(echo "$docker_status" | tail -n +2 | jq -R . | jq -s . 2>/dev/null || echo '[]'),
    "load_average": "$(uptime | awk -F'load averages:' '{print $2}' | xargs)"
}
EOF
}

# 生成完整的健康报告
generate_health_report() {
    echo "📋 生成健康报告..."
    
    # 检查各个服务
    backend_health=$(check_service_health "Backend" "$BASE_URL")
    vision_health=$(check_service_health "Vision" "$VISION_URL")
    agent_health=$(check_service_health "Agent" "$AGENT_URL")
    frontend_health=$(check_service_health "Frontend" "$FRONTEND_URL")
    
    # 检查API性能
    backend_perf=$(check_api_performance "Backend" "$BASE_URL")
    vision_perf=$(check_api_performance "Vision" "$VISION_URL")
    
    # 检查系统资源
    system_resources=$(check_system_resources)
    
    # 生成综合报告
    report=$(cat << EOF
{
    "timestamp": "$(date -Iseconds)",
    "report_id": "$TIMESTAMP",
    "services": {
        "backend": $backend_health,
        "vision": $vision_health,
        "agent": $agent_health,
        "frontend": $frontend_health
    },
    "performance": {
        "backend_api": $backend_perf,
        "vision_api": $vision_perf
    },
    "system": $system_resources,
    "summary": {
        "healthy_services": $(echo "$backend_health $vision_health $agent_health $frontend_health" | jq -s 'map(select(.status == "healthy")) | length'),
        "total_services": 4,
        "overall_status": "$(echo "$backend_health $vision_health $agent_health $frontend_health" | jq -s 'if map(select(.status == "healthy")) | length == 4 then "healthy" elif map(select(.status == "healthy")) | length >= 2 then "degraded" else "critical" end' -r)"
    }
}
EOF
    )
    
    echo "$report" | jq . > "$REPORT_FILE"
    echo "✅ 健康报告已保存: $REPORT_FILE"
    
    # 输出摘要
    echo ""
    echo "📊 健康检查摘要:"
    echo "================================"
    echo "$report" | jq -r '
        "总体状态: \(.summary.overall_status)",
        "健康服务: \(.summary.healthy_services)/\(.summary.total_services)",
        "CPU使用率: \(.system.cpu_usage_percent)%",
        "内存使用率: \(.system.memory_usage_percent)%",
        "磁盘使用率: \(.system.disk_usage_percent)%"
    '
    
    # 如果有问题，显示详细信息
    if [ "$(echo "$report" | jq -r '.summary.overall_status')" != "healthy" ]; then
        echo ""
        echo "⚠️  发现问题:"
        echo "$report" | jq -r '.services | to_entries[] | select(.value.status != "healthy") | "- \(.key): \(.value.status)"'
    fi
}

# 性能压力测试
run_stress_test() {
    echo "🔥 运行性能压力测试..."
    
    if ! command -v ab &> /dev/null; then
        echo "⚠️  Apache Bench (ab) 未安装，跳过压力测试"
        return
    fi
    
    # 测试后端API
    echo "📊 测试后端API性能..."
    ab_result=$(ab -n 100 -c 10 "$BASE_URL/health" 2>/dev/null | grep "Requests per second\|Time per request" || echo "压力测试失败")
    echo "$ab_result"
    
    # 保存压力测试结果
    stress_report="$REPORT_DIR/stress_test_$TIMESTAMP.txt"
    ab -n 100 -c 10 "$BASE_URL/health" > "$stress_report" 2>&1 || echo "压力测试失败" > "$stress_report"
    echo "📋 压力测试报告已保存: $stress_report"
}

# 主执行逻辑
main() {
    case "${1:-health}" in
        "health")
            generate_health_report
            ;;
        "stress")
            run_stress_test
            ;;
        "all")
            generate_health_report
            echo ""
            run_stress_test
            ;;
        *)
            echo "用法: $0 [health|stress|all]"
            echo "  health: 运行健康检查 (默认)"
            echo "  stress: 运行压力测试"
            echo "  all: 运行所有测试"
            exit 1
            ;;
    esac
}

# 检查依赖
if ! command -v jq &> /dev/null; then
    echo "❌ jq 未安装，请先安装 jq"
    exit 1
fi

if ! command -v curl &> /dev/null; then
    echo "❌ curl 未安装，请先安装 curl"
    exit 1
fi

# 执行主函数
main "$@"