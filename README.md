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

## 使用 docker-compose（可选）

```bash
docker compose up --build
```

端口：后端 8080，前端 5173，vision 8001，agent 8002。

## API 速览

- POST `/api/events/vision` 接收 YOLO 事件
- GET `/api/events/stream` SSE 实时流
- GET `/api/events/recent?minutes=10` 最近事件
- GET/POST/PUT/DELETE `/api/zones` 危险区域
- POST `/api/agent/insights` Agent 回传

## 数据库

SQLite 文件位于 `data/baby_safety.db`，JPA `ddl-auto=update` 自动建表。

实时检测3岁以内宝宝活动安全轨迹，并进行危险区域与动作预警。

## 模块
- backend: Spring Boot 3 (Java 21), SQLite, JPA, Caffeine, SSE
- frontend: Vite + React + TypeScript
- services/vision: FastAPI + YOLO(ultralytics)
- services/agent: FastAPI + 规则/LLM推理

## 开发
- 本地直接运行各子模块
- 或使用 docker-compose 编排
