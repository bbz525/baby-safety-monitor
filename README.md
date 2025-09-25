# Baby Safety Monitor

## 快速开始（本地）

1. 启动后端（需 Java 21 与 Maven）
   - `cd backend && ./mvnw spring-boot:run`

2. 启动前端
   - `cd frontend && npm install && npm run dev`
   - 浏览器打开 `http://localhost:5173`

3. 启动 Python 服务（可选）
   - 视觉：`cd services/vision && pip install -r requirements.txt && uvicorn app:app --reload --port 8001`
   - Agent：`cd services/agent && pip install -r requirements.txt && uvicorn app:app --reload --port 8002`

## 使用 docker-compose（推荐）

```bash
docker compose up --build
```

端口：后端 8080，前端 5173，vision 8001，agent 8002。

## 摄像头接入

### 支持的摄像头类型

1. **RTSP摄像头**（推荐）
   ```bash
   # 添加RTSP摄像头
   curl -X POST http://localhost:8001/cameras \
     -H "Content-Type: application/json" \
     -d '{
       "name": "客厅摄像头",
       "source": "rtsp://admin:password@192.168.1.100:554/stream1",
       "type": "rtsp",
       "fps": 1.0,
       "resolution": 640
     }'
   ```

2. **HTTP摄像头**
   ```bash
   # 添加HTTP摄像头
   curl -X POST http://localhost:8001/cameras \
     -H "Content-Type: application/json" \
     -d '{
       "name": "卧室摄像头",
       "source": "http://192.168.1.101:8080/video",
       "type": "http",
       "fps": 2.0,
       "resolution": 1280
     }'
   ```

3. **本地视频文件**
   ```bash
   # 添加本地视频文件
   curl -X POST http://localhost:8001/cameras \
     -H "Content-Type: application/json" \
     -d '{
       "name": "测试视频",
       "source": "/app/data/test_video.mp4",
       "type": "file",
       "fps": 1.0,
       "resolution": 640
     }'
   ```

### 摄像头管理

```bash
# 列出所有摄像头
curl http://localhost:8001/cameras

# 启动摄像头
curl -X POST http://localhost:8001/cameras/{camera_id}/start

# 停止摄像头
curl -X POST http://localhost:8001/cameras/{camera_id}/stop

# 删除摄像头
curl -X DELETE http://localhost:8001/cameras/{camera_id}
```

### 常见RTSP URL格式

- **海康威视**: `rtsp://admin:password@ip:554/Streaming/Channels/101`
- **大华**: `rtsp://admin:password@ip:554/cam/realmonitor?channel=1&subtype=0`
- **通用格式**: `rtsp://username:password@ip:port/path`

## API 速览

### 后端API
- POST `/api/events/vision` 接收 YOLO 事件
- GET `/api/events/stream` SSE 实时流
- GET `/api/events/recent?minutes=10` 最近事件
- GET/POST/PUT/DELETE `/api/zones` 危险区域
- POST `/api/agent/insights` Agent 回传

### Vision服务API
- POST `/cameras` 创建摄像头
- GET `/cameras` 列出摄像头
- GET `/cameras/{id}` 获取摄像头详情
- PUT `/cameras/{id}` 更新摄像头
- DELETE `/cameras/{id}` 删除摄像头
- POST `/cameras/{id}/start` 启动摄像头
- POST `/cameras/{id}/stop` 停止摄像头
- POST `/infer` 单次推理（文件/URL）
- GET `/last.jpg` 获取最后处理的帧

## 数据库

SQLite 文件位于 `data/baby_safety.db`，JPA `ddl-auto=update` 自动建表。

实时检测3岁以内宝宝活动安全轨迹，并进行危险区域与动作预警。

## 模块
- backend: Spring Boot 3 (Java 21), SQLite, JPA, Caffeine, SSE
- frontend: Vite + React + TypeScript
- services/vision: FastAPI + YOLO(ultralytics) + OpenCV
- services/agent: FastAPI + 规则/LLM推理

## 测试

```bash
# 运行Vision服务测试
cd services/vision
python -m pytest test_vision.py -v
```

## 开发
- 本地直接运行各子模块
- 或使用 docker-compose 编排
