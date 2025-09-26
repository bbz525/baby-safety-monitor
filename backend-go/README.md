# 婴儿安全监控系统 - Go后端

基于Go语言重构的高性能后端服务，提供实时事件处理、SSE推送、告警通知等功能。

## 🚀 特性

- **高性能**: 基于Go语言，支持高并发处理
- **实时推送**: SSE (Server-Sent Events) 实时事件推送
- **数据存储**: SQLite数据库，轻量级部署
- **通知集成**: 钉钉通知、浏览器通知
- **RESTful API**: 完整的REST API接口
- **容器化**: Docker支持，易于部署

## 📋 系统要求

- Go 1.21+
- SQLite3
- 4GB+ RAM (推荐)

## 🔧 快速开始

### 1. 环境准备

```bash
# 安装Go 1.21+
# macOS
brew install go

# Ubuntu/Debian
sudo apt update
sudo apt install golang-go

# 验证安装
go version
```

### 2. 下载依赖

```bash
cd backend-go
go mod download
```

### 3. 启动服务

```bash
# 使用启动脚本
./scripts/start.sh

# 或直接运行
go run ./cmd/server
```

### 4. 验证服务

```bash
# 健康检查
curl http://localhost:8080/health

# 服务信息
curl http://localhost:8080/api/info
```

## 📡 API接口

### 健康检查
- `GET /health` - 健康检查
- `GET /api/info` - 服务信息

### 视觉事件
- `POST /api/events/vision` - 创建视觉事件
- `GET /api/events/recent?minutes=10` - 获取最近事件
- `GET /api/events/track/{trackId}` - 根据TrackID获取事件
- `GET /api/events/stats` - 事件统计
- `GET /api/events/stream` - SSE事件流

### 告警管理
- `POST /api/alerts` - 创建告警
- `GET /api/alerts/recent?minutes=60` - 获取最近告警
- `GET /api/alerts/level/{level}` - 根据级别获取告警
- `GET /api/alerts/stats` - 告警统计

### 危险区域
- `POST /api/zones` - 创建危险区域
- `GET /api/zones` - 获取所有危险区域
- `GET /api/zones/enabled` - 获取启用的危险区域
- `GET /api/zones/{id}` - 获取指定危险区域
- `PUT /api/zones/{id}` - 更新危险区域
- `DELETE /api/zones/{id}` - 删除危险区域

## 🔧 配置

### 环境变量

```bash
# 服务配置
export PORT=8080
export GIN_MODE=release

# 数据库配置
export DB_DSN="data/baby_safety.db"

# 钉钉通知配置
export DINGTALK_WEBHOOK="https://oapi.dingtalk.com/robot/send?access_token=xxx"
export DINGTALK_SECRET="your_secret"

# 日志配置
export LOG_LEVEL=info
```

### 配置文件

编辑 `config.yaml`:

```yaml
server:
  port: 8080
  mode: release

database:
  driver: sqlite
  dsn: "data/baby_safety.db"

logging:
  level: info
  format: text

notification:
  dingtalk:
    webhook: ""
    secret: ""
```

## 🐳 Docker部署

### 构建镜像

```bash
docker build -t baby-safety-backend-go .
```

### 运行容器

```bash
docker run -d \
  --name baby-safety-backend \
  -p 8080:8080 \
  -v $(pwd)/data:/app/data \
  -e DINGTALK_WEBHOOK="your_webhook" \
  -e DINGTALK_SECRET="your_secret" \
  baby-safety-backend-go
```

### Docker Compose

```yaml
version: '3.8'
services:
  backend-go:
    build: ./backend-go
    ports:
      - "8080:8080"
    volumes:
      - ./data:/app/data
    environment:
      - DINGTALK_WEBHOOK=${DINGTALK_WEBHOOK}
      - DINGTALK_SECRET=${DINGTALK_SECRET}
    restart: unless-stopped
```

## 📊 性能对比

| 指标 | Java Spring Boot | Go Gin |
|------|------------------|--------|
| 启动时间 | 15-30s | 1-3s |
| 内存占用 | 200-500MB | 20-50MB |
| 并发处理 | 1000 req/s | 10000+ req/s |
| 响应延迟 | 50-100ms | 5-20ms |
| 二进制大小 | 100MB+ | 10-20MB |

## 🔍 监控和日志

### 日志级别

```bash
# 设置日志级别
export LOG_LEVEL=debug  # debug, info, warn, error
```

### 健康检查

```bash
# 检查服务状态
curl http://localhost:8080/health

# 检查SSE连接数
curl http://localhost:8080/api/events/stats
```

### 性能监控

```bash
# 查看Go运行时信息
curl http://localhost:8080/debug/pprof/

# 内存使用情况
curl http://localhost:8080/debug/pprof/heap

# CPU使用情况
curl http://localhost:8080/debug/pprof/profile
```

## 🧪 测试

### 单元测试

```bash
# 运行所有测试
go test ./...

# 运行特定包测试
go test ./internal/controller

# 生成测试覆盖率
go test -cover ./...
```

### 集成测试

```bash
# 启动测试服务
go run ./cmd/server &

# 运行集成测试
go test -tags=integration ./tests/...
```

### 压力测试

```bash
# 使用hey进行压力测试
hey -n 10000 -c 100 http://localhost:8080/health

# 使用wrk进行压力测试
wrk -t12 -c400 -d30s http://localhost:8080/health
```

## 🔧 开发指南

### 项目结构

```
backend-go/
├── cmd/
│   └── server/          # 主程序入口
├── internal/
│   ├── controller/      # 控制器层
│   ├── models/          # 数据模型
│   ├── repository/      # 数据访问层
│   ├── service/         # 业务逻辑层
│   └── database/        # 数据库连接
├── scripts/             # 脚本文件
├── config.yaml          # 配置文件
├── go.mod              # Go模块文件
├── go.sum              # 依赖校验
└── Dockerfile          # Docker配置
```

### 添加新功能

1. **创建模型**: 在 `internal/models/` 中定义数据结构
2. **创建仓库**: 在 `internal/repository/` 中实现数据访问
3. **创建服务**: 在 `internal/service/` 中实现业务逻辑
4. **创建控制器**: 在 `internal/controller/` 中实现API接口
5. **注册路由**: 在 `cmd/server/main.go` 中注册路由

### 代码规范

```bash
# 格式化代码
go fmt ./...

# 静态检查
go vet ./...

# 使用golangci-lint
golangci-lint run
```

## 🚀 部署建议

### 生产环境

1. **使用反向代理**: Nginx或Apache
2. **启用HTTPS**: 使用Let's Encrypt
3. **配置日志**: 使用结构化日志
4. **监控告警**: 集成Prometheus + Grafana
5. **备份策略**: 定期备份SQLite数据库

### 性能优化

1. **连接池**: 配置数据库连接池
2. **缓存策略**: 使用Redis缓存热点数据
3. **负载均衡**: 多实例部署
4. **资源限制**: 设置内存和CPU限制

## 📝 更新日志

### v1.0.0 (2025-09-25)
- 初始版本发布
- 完整的REST API
- SSE实时推送
- 钉钉通知集成
- Docker支持

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 📄 许可证

MIT License

## 📞 支持

如有问题，请提交Issue或联系开发团队。
