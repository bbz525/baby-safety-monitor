# Mac摄像头接入指南

## 🎯 快速开始

### 1. 自动设置（推荐）
```bash
python scripts/mac_camera_simple.py
```

### 2. 手动设置
```bash
# 1. 添加Mac摄像头
curl -X POST http://localhost:8001/cameras \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mac内置摄像头",
    "source": "0",
    "type": "mac_camera",
    "fps": 1.0,
    "resolution": 640
  }'

# 2. 启动摄像头
curl -X POST http://localhost:8001/cameras/{camera_id}/start

# 3. 查看状态
curl http://localhost:8001/cameras/{camera_id}
```

## 🔧 摄像头索引说明

Mac系统可能有多个摄像头设备，常见索引：
- `0` - 内置摄像头（默认）
- `1` - 外接USB摄像头
- `2` - iPhone摄像头（如果连接）

## 📱 支持的摄像头类型

1. **Mac内置摄像头** - 索引0
2. **外接USB摄像头** - 索引1,2,3...
3. **iPhone摄像头** - 通过USB连接

## ⚙️ 权限设置

如果遇到权限问题：

1. **系统偏好设置** > **安全性与隐私** > **隐私** > **摄像头**
2. 确保以下应用有摄像头权限：
   - 终端 (Terminal)
   - Python
   - 或者整个系统

## 🚀 使用示例

### 基本操作
```bash
# 查看所有摄像头
curl http://localhost:8001/cameras

# 启动摄像头
curl -X POST http://localhost:8001/cameras/{camera_id}/start

# 停止摄像头
curl -X POST http://localhost:8001/cameras/{camera_id}/stop

# 删除摄像头
curl -X DELETE http://localhost:8001/cameras/{camera_id}
```

### 监控检测结果
```bash
# 查看最近事件（需要后端服务运行）
curl http://localhost:8080/api/events/recent?minutes=5

# 查看SSE流（需要后端服务运行）
curl http://localhost:8080/api/events/stream
```

## 🔍 故障排除

### 问题1：摄像头无法打开
**解决方案：**
1. 检查摄像头是否被其他应用占用
2. 重启终端
3. 检查系统权限设置

### 问题2：无法检测到人员
**解决方案：**
1. 确保光线充足
2. 调整摄像头角度
3. 检查YOLO模型是否正常加载

### 问题3：权限被拒绝
**解决方案：**
1. 手动打开Photo Booth或FaceTime授权权限
2. 在系统偏好设置中手动授权
3. 重启应用

## 📊 性能优化

### 调整参数
```json
{
  "fps": 0.5,        // 降低帧率减少CPU使用
  "resolution": 320,  // 降低分辨率提高性能
  "enabled": true
}
```

### 监控资源使用
```bash
# 查看进程资源使用
top -pid $(pgrep -f "uvicorn app:app")

# 查看摄像头状态
curl http://localhost:8001/cameras/{camera_id}
```

## 🎉 成功标志

当Mac摄像头成功接入后，你应该看到：
1. 摄像头状态为 `running`
2. 没有 `last_error`
3. 能够检测到人员并生成事件
4. 前端界面显示实时检测结果

## 📝 注意事项

1. **隐私保护**：摄像头数据仅在本地处理，不会上传到云端
2. **性能影响**：YOLO推理会消耗CPU资源，建议在性能较好的设备上运行
3. **电池续航**：长时间运行会影响MacBook电池续航
4. **散热**：长时间运行可能产生热量，注意设备散热

## 🔗 相关链接

- [Vision服务API文档](http://localhost:8001/docs)
- [后端API文档](http://localhost:8080/swagger-ui.html)
- [前端界面](http://localhost:5173)
