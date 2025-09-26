#!/bin/bash

# 婴儿安全监控系统 - Go后端性能测试脚本

set -e

echo "=== 婴儿安全监控系统 Go后端性能测试 ==="

# 检查依赖
if ! command -v curl &> /dev/null; then
    echo "❌ curl未安装"
    exit 1
fi

if ! command -v hey &> /dev/null; then
    echo "⚠️  hey未安装，将使用curl进行基础测试"
    USE_HEY=false
else
    USE_HEY=true
fi

# 测试配置
BASE_URL="http://localhost:8082"
TEST_DURATION=10
CONCURRENT_USERS=50
TOTAL_REQUESTS=1000

echo "📊 测试配置:"
echo "   服务地址: $BASE_URL"
echo "   测试时长: ${TEST_DURATION}s"
echo "   并发用户: $CONCURRENT_USERS"
echo "   总请求数: $TOTAL_REQUESTS"
echo ""

# 检查服务状态
echo "🔍 检查服务状态..."
if ! curl -s "$BASE_URL/health" > /dev/null; then
    echo "❌ 服务未启动，请先启动Go后端服务"
    exit 1
fi
echo "✅ 服务运行正常"
echo ""

# 基础功能测试
echo "🧪 基础功能测试..."

# 1. 健康检查
echo "1. 健康检查测试"
HEALTH_START=$(date +%s)
curl -s "$BASE_URL/health" > /dev/null
HEALTH_END=$(date +%s)
HEALTH_TIME=$((HEALTH_END - HEALTH_START))
echo "   响应时间: ${HEALTH_TIME}s"
echo ""

# 2. 创建视觉事件
echo "2. 创建视觉事件测试"
EVENT_START=$(date +%s%3N)
curl -s -X POST "$BASE_URL/api/events/vision" \
  -H "Content-Type: application/json" \
  -d '{"trackId": "perf-test-1", "bbox": [100, 120, 60, 80], "action": "walk", "riskScore": 0.3}' \
  > /dev/null
EVENT_END=$(date +%s%3N)
EVENT_TIME=$((EVENT_END - EVENT_START))
echo "   响应时间: ${EVENT_TIME}ms"
echo ""

# 3. 查询最近事件
echo "3. 查询最近事件测试"
QUERY_START=$(date +%s%3N)
curl -s "$BASE_URL/api/events/recent?minutes=10" > /dev/null
QUERY_END=$(date +%s%3N)
QUERY_TIME=$((QUERY_END - QUERY_START))
echo "   响应时间: ${QUERY_TIME}ms"
echo ""

# 4. 创建告警
echo "4. 创建告警测试"
ALERT_START=$(date +%s%3N)
curl -s -X POST "$BASE_URL/api/alerts" \
  -H "Content-Type: application/json" \
  -d '{"trackId": "perf-test-1", "level": "high", "reason": "性能测试告警", "detailsJson": "{\"test\": true}"}' \
  > /dev/null
ALERT_END=$(date +%s%3N)
ALERT_TIME=$((ALERT_END - ALERT_START))
echo "   响应时间: ${ALERT_TIME}ms"
echo ""

# 性能压力测试
if [ "$USE_HEY" = true ]; then
    echo "🚀 性能压力测试 (使用hey)..."
    
    # 健康检查压力测试
    echo "1. 健康检查压力测试"
    hey -n $TOTAL_REQUESTS -c $CONCURRENT_USERS -m GET "$BASE_URL/health"
    echo ""
    
    # 事件查询压力测试
    echo "2. 事件查询压力测试"
    hey -n $TOTAL_REQUESTS -c $CONCURRENT_USERS -m GET "$BASE_URL/api/events/recent?minutes=10"
    echo ""
    
    # 事件创建压力测试
    echo "3. 事件创建压力测试"
    hey -n $TOTAL_REQUESTS -c $CONCURRENT_USERS -m POST \
      -H "Content-Type: application/json" \
      -d '{"trackId": "stress-test", "bbox": [100, 120, 60, 80], "action": "run", "riskScore": 0.5}' \
      "$BASE_URL/api/events/vision"
    echo ""
    
else
    echo "🚀 性能压力测试 (使用curl)..."
    
    # 简单的并发测试
    echo "1. 并发健康检查测试"
    CONCURRENT_START=$(date +%s%3N)
    
    for i in $(seq 1 $CONCURRENT_USERS); do
        curl -s "$BASE_URL/health" > /dev/null &
    done
    wait
    
    CONCURRENT_END=$(date +%s%3N)
    CONCURRENT_TIME=$((CONCURRENT_END - CONCURRENT_START))
    echo "   $CONCURRENT_USERS 个并发请求完成时间: ${CONCURRENT_TIME}ms"
    echo "   平均响应时间: $((CONCURRENT_TIME / CONCURRENT_USERS))ms"
    echo ""
fi

# 内存和资源使用情况
echo "📈 资源使用情况..."
if command -v ps &> /dev/null; then
    # 查找Go进程
    GO_PID=$(pgrep -f "bin/server" | head -1)
    if [ ! -z "$GO_PID" ]; then
        echo "Go进程PID: $GO_PID"
        ps -p $GO_PID -o pid,ppid,pcpu,pmem,rss,vsz,comm
    fi
fi
echo ""

# 数据库文件大小
if [ -f "data/baby_safety.db" ]; then
    DB_SIZE=$(du -h data/baby_safety.db | cut -f1)
    echo "数据库文件大小: $DB_SIZE"
fi
echo ""

# 性能总结
echo "📊 性能测试总结:"
echo "   健康检查响应时间: ${HEALTH_TIME}ms"
echo "   事件创建响应时间: ${EVENT_TIME}ms"
echo "   事件查询响应时间: ${QUERY_TIME}ms"
echo "   告警创建响应时间: ${ALERT_TIME}ms"
echo ""

# 性能评级
if [ $HEALTH_TIME -lt 10 ]; then
    echo "✅ 健康检查性能: 优秀 (< 10ms)"
elif [ $HEALTH_TIME -lt 50 ]; then
    echo "✅ 健康检查性能: 良好 (< 50ms)"
else
    echo "⚠️  健康检查性能: 需要优化 (> 50ms)"
fi

if [ $EVENT_TIME -lt 50 ]; then
    echo "✅ 事件创建性能: 优秀 (< 50ms)"
elif [ $EVENT_TIME -lt 100 ]; then
    echo "✅ 事件创建性能: 良好 (< 100ms)"
else
    echo "⚠️  事件创建性能: 需要优化 (> 100ms)"
fi

echo ""
echo "🎉 性能测试完成！"
echo ""
echo "💡 优化建议:"
echo "   1. 使用连接池优化数据库连接"
echo "   2. 启用Gzip压缩减少网络传输"
echo "   3. 使用Redis缓存热点数据"
echo "   4. 配置负载均衡支持多实例"
echo "   5. 监控内存使用和GC性能"
