#!/bin/bash

# 婴儿安全监控系统快速启动脚本

set -e

echo "=== 婴儿安全监控系统启动 ==="

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker未运行，请先启动Docker"
    exit 1
fi

echo "✅ Docker运行正常"

# 创建必要的目录
mkdir -p data/models
mkdir -p data

echo "📁 创建数据目录完成"

# 启动服务
echo "🚀 启动所有服务..."
docker compose up -d --build

echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "🔍 检查服务状态..."

services=("backend:8080" "frontend:5173" "vision:8001" "agent:8002")

for service in "${services[@]}"; do
    name=$(echo $service | cut -d: -f1)
    port=$(echo $service | cut -d: -f2)
    
    if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
        echo "✅ $name 服务运行正常 (端口 $port)"
    else
        echo "❌ $name 服务未响应 (端口 $port)"
    fi
done

echo ""
echo "🌐 服务访问地址:"
echo "  前端界面: http://localhost:5173"
echo "  后端API: http://localhost:8080"
echo "  Vision服务: http://localhost:8001"
echo "  Agent服务: http://localhost:8002"
echo ""
echo "📖 使用说明:"
echo "  1. 打开浏览器访问 http://localhost:5173"
echo "  2. 添加摄像头: curl -X POST http://localhost:8001/cameras -H 'Content-Type: application/json' -d '{\"name\":\"我的摄像头\",\"source\":\"rtsp://user:pass@ip:554/stream\",\"type\":\"rtsp\"}'"
echo "  3. 启动摄像头: curl -X POST http://localhost:8001/cameras/{camera_id}/start"
echo "  4. 查看摄像头: curl http://localhost:8001/cameras"
echo ""
echo "🛑 停止服务: docker compose down"
echo "📊 查看日志: docker compose logs -f"
echo ""
echo "=== 启动完成 ==="
