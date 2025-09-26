#!/bin/bash

# 婴儿安全监控系统 - 部署脚本

set -e

echo "🚀 婴儿安全监控系统部署脚本"
echo "================================"

# 配置参数
ENV=${1:-dev}  # dev, prod
PROFILE=${2:-default}  # default, java, monitoring

# 检查Docker和Docker Compose
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose未安装，请先安装Docker Compose"
    exit 1
fi

# 创建必要的目录
echo "📁 创建目录结构..."
mkdir -p data/{models,logs}
mkdir -p logs/{backend,frontend,vision,agent}
mkdir -p monitoring/{prometheus,grafana}

# 下载YOLO模型（如果不存在）
if [ ! -f "data/models/yolov8n.pt" ]; then
    echo "📥 下载YOLO模型..."
    curl -L "https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt" -o "data/models/yolov8n.pt"
    echo "✅ YOLO模型下载完成"
fi

# 设置环境变量
echo "⚙️  配置环境变量..."
if [ ! -f ".env" ]; then
    cp .env.example .env 2>/dev/null || cat > .env << EOF
# 钉钉通知配置
DINGTALK_WEBHOOK=
DINGTALK_SECRET=

# Grafana配置
GRAFANA_PASSWORD=admin123

# 日志级别
LOG_LEVEL=info
EOF
    echo "✅ 已创建 .env 文件，请根据需要修改配置"
fi

# 构建和启动服务
case $ENV in
  "dev")
    echo "🔧 启动开发环境..."
    COMPOSE_FILE="docker-compose.yml"
    ;;
  "prod")
    echo "🚀 启动生产环境..."
    COMPOSE_FILE="docker-compose.prod.yml"
    ;;
  *)
    echo "❌ 无效的环境: $ENV (支持: dev, prod)"
    exit 1
    ;;
esac

# 添加profile支持
PROFILE_ARGS=""
if [ "$PROFILE" != "default" ]; then
    PROFILE_ARGS="--profile $PROFILE"
fi

echo "🔨 构建镜像..."
docker-compose -f $COMPOSE_FILE $PROFILE_ARGS build

echo "🚀 启动服务..."
docker-compose -f $COMPOSE_FILE $PROFILE_ARGS up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 健康检查
echo "🔍 检查服务状态..."
check_service() {
    local service=$1
    local url=$2
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo "✅ $service 服务正常"
            return 0
        fi
        echo "⏳ 等待 $service 服务启动... ($attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done
    
    echo "❌ $service 服务启动失败"
    return 1
}

# 检查各服务
if [ "$ENV" = "dev" ]; then
    check_service "Go后端" "http://localhost:8080/health"
    check_service "Vision服务" "http://localhost:8001/health"
    check_service "Agent服务" "http://localhost:8002/health"
    check_service "前端" "http://localhost:5173"
else
    check_service "Nginx" "http://localhost/health"
fi

# 显示访问信息
echo ""
echo "🎉 部署完成！"
echo "================================"

if [ "$ENV" = "dev" ]; then
    echo "📱 前端界面: http://localhost:5173"
    echo "🔧 Go后端API: http://localhost:8080"
    echo "👁️ Vision服务: http://localhost:8001"
    echo "🤖 Agent服务: http://localhost:8002"
    
    if [ "$PROFILE" = "monitoring" ] || [ "$PROFILE" = "all" ]; then
        echo "📊 Prometheus: http://localhost:9090"
        echo "📈 Grafana: http://localhost:3000 (admin/admin123)"
    fi
else
    echo "🌐 Web界面: http://localhost"
    echo "📊 监控面板: http://localhost:3000 (admin/admin123)"
fi

echo ""
echo "💡 常用命令："
echo "   查看日志: docker-compose -f $COMPOSE_FILE logs -f [service]"
echo "   停止服务: docker-compose -f $COMPOSE_FILE down"
echo "   重启服务: docker-compose -f $COMPOSE_FILE restart [service]"
echo "   查看状态: docker-compose -f $COMPOSE_FILE ps"

# 如果是首次部署，显示配置提示
if [ ! -f ".deployed" ]; then
    echo ""
    echo "🔧 首次部署配置提示："
    echo "   1. 配置钉钉通知：编辑 .env 文件中的 DINGTALK_WEBHOOK 和 DINGTALK_SECRET"
    echo "   2. 添加摄像头：访问前端界面的摄像头管理页面"
    echo "   3. 测试检测：可以使用 Vision 服务的 /simulate 接口进行测试"
    touch .deployed
fi

echo ""
echo "✨ 祝您使用愉快！"