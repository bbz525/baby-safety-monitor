#!/bin/bash

# 简化的Go后端测试脚本

echo "=== Go后端基础测试 ==="

BASE_URL="http://localhost:8082"

# 1. 健康检查
echo "1. 健康检查"
curl -s "$BASE_URL/health" | jq .
echo ""

# 2. 创建视觉事件
echo "2. 创建视觉事件"
curl -X POST "$BASE_URL/api/events/vision" \
  -H "Content-Type: application/json" \
  -d '{"trackId": "test-2", "bbox": [150, 150, 80, 100], "action": "crawl", "riskScore": 0.6}' | jq .
echo ""

# 3. 查询最近事件
echo "3. 查询最近事件"
curl -s "$BASE_URL/api/events/recent?minutes=10" | jq .
echo ""

# 4. 创建告警
echo "4. 创建告警"
curl -X POST "$BASE_URL/api/alerts" \
  -H "Content-Type: application/json" \
  -d '{"trackId": "test-2", "level": "medium", "reason": "检测到爬行行为", "detailsJson": "{\"action\": \"crawl\", \"risk_score\": 0.6}"}' | jq .
echo ""

# 5. 查询告警
echo "5. 查询最近告警"
curl -s "$BASE_URL/api/alerts/recent?minutes=10" | jq .
echo ""

# 6. 创建危险区域
echo "6. 创建危险区域"
curl -X POST "$BASE_URL/api/zones" \
  -H "Content-Type: application/json" \
  -d '{"name": "厨房危险区", "polygonJson": "[[300,300],[400,300],[400,400],[300,400]]", "level": "high", "enabled": true}' | jq .
echo ""

# 7. 查询危险区域
echo "7. 查询危险区域"
curl -s "$BASE_URL/api/zones" | jq .
echo ""

# 8. 并发测试
echo "8. 并发测试 (10个请求)"
for i in {1..10}; do
    curl -s "$BASE_URL/health" > /dev/null &
done
wait
echo "并发测试完成"
echo ""

# 9. 资源使用情况
echo "9. 资源使用情况"
GO_PID=$(pgrep -f "bin/server" | head -1)
if [ ! -z "$GO_PID" ]; then
    echo "Go进程信息:"
    ps -p $GO_PID -o pid,ppid,pcpu,pmem,rss,vsz,comm
fi

if [ -f "data/baby_safety.db" ]; then
    echo "数据库大小: $(du -h data/baby_safety.db | cut -f1)"
fi

echo ""
echo "✅ 测试完成！"
