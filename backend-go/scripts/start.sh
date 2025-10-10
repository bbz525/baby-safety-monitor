#!/bin/bash
全监控系统 Go后端启动脚本

set -e

echo "=== 婴儿安全监控系统 Go后端启动 ==="

# 检查Go环境
if ! command -v go &> /dev/null; then
    echo "❌ Go未安装，请先安装Go 1.21+"
    exit 1
fi

echo "✅ Go环境检查通过"

# 检查Go版本
GO_VERSION=$(go version | awk '{print $3}' | sed 's/go//')
REQUIRED_VERSION="1.25"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$GO_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Go版本过低，需要1.21+，当前版本: $GO_VERSION"
    exit 1
fi

echo "✅ Go版本检查通过: $GO_VERSION"

# 创建数据目录
mkdir -p data
echo "📁 数据目录已创建"

# 下载依赖
echo "📦 下载Go依赖..."
go mod download

# 构建应用
echo "🔨 构建应用..."
go build -o bin/server ./cmd/server

# 设置环境变量
export GIN_MODE=release
export PORT=8080

# 启动应用
echo "🚀 启动Go后端服务..."
echo "   端口: 8080"
echo "   数据目录: ./data"
echo "   日志级别: info"
echo ""
echo "⏹️  按 Ctrl+C 停止服务"
echo ""

./bin/server
