# Mac摄像头快速接入指南

## 🚀 快速开始

### 1. 启动Vision服务
```bash
cd /Users/bbc/IdeaProjects/baby-safety-monitor/services/vision
python test_app.py
```

### 2. 添加Mac摄像头
```bash
curl -X POST http://localhost:8004/cameras \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mac内置摄像头",
    "source": "0",
    "type": "mac_camera",
    "fps": 1.0,
    "resolution": 640
  }'
```

### 3. 查看摄像头列表
```bash
curl http://localhost:8004/cameras
```

### 4. 查看特定摄像头
```bash
curl http://localhost:8004/cameras/{camera_id}
```

## 📱 摄像头配置说明

### 摄像头类型
- `mac_camera` - Mac内置摄像头
- `rtsp` - RTSP网络摄像头
- `http` - HTTP视频流
- `file` - 本地视频文件

### 摄像头索引
- `0` - Mac内置摄像头（默认）
- `1` - 外接USB摄像头
- `2` - iPhone摄像头（通过USB连接）

### 配置参数
- `fps` - 帧率（建议0.5-2.0）
- `resolution` - 分辨率（320, 640, 1280）
- `enabled` - 是否启用

## 🔧 常用命令

### 查看所有摄像头
```bash
curl http://localhost:8004/cameras
```

### 添加不同类型的摄像头
```bash
# Mac内置摄像头
curl -X POST http://localhost:8004/cameras \
  -H "Content-Type: application/json" \
  -d '{"name": "Mac摄像头", "source": "0", "type": "mac_camera", "fps": 1.0, "resolution": 640}'

# 外接USB摄像头
curl -X POST http://localhost:8004/cameras \
  -H "Content-Type: application/json" \
  -d '{"name": "USB摄像头", "source": "1", "type": "mac_camera", "fps": 1.0, "resolution": 640}'

# RTSP网络摄像头
curl -X POST http://localhost:8004/cameras \
  -H "Content-Type: application/json" \
  -d '{"name": "网络摄像头", "source": "rtsp://user:pass@ip:554/stream", "type": "rtsp", "fps": 1.0, "resolution": 640}'
```

### 删除摄像头
```bash
curl -X DELETE http://localhost:8004/cameras/{camera_id}
```

## 🎯 当前状态

- **服务端口**: 8004
- **摄像头ID**: `355d7aeb-00cc-47d2-baa2-8f2fe4c2bf0d`
- **状态**: 已添加，待启动

## ⚠️ 注意事项

1. **权限设置**: 确保终端有摄像头权限
2. **端口占用**: 如果8004端口被占用，可以修改test_app.py中的端口号
3. **摄像头占用**: 确保摄像头没有被其他应用占用

## 🔍 故障排除

### 问题1: 端口被占用
```bash
# 查看端口占用
lsof -i :8004

# 修改端口
# 编辑 test_app.py，修改 port=8004 为其他端口
```

### 问题2: 摄像头无法访问
```bash
# 测试摄像头权限
python scripts/test_mac_camera.py

# 检查系统权限
# 系统偏好设置 > 安全性与隐私 > 隐私 > 摄像头
```

### 问题3: 服务无法启动
```bash
# 检查Python依赖
pip install -r requirements.txt

# 检查代码语法
python -m py_compile test_app.py
```

## 📊 下一步

1. **启动检测功能** - 添加YOLO人员检测
2. **连接后端** - 实现事件推送到后端
3. **前端显示** - 在Web界面显示检测结果
4. **告警系统** - 实现危险行为告警

## 🎉 成功标志

当看到以下输出时，说明Mac摄像头已成功接入：
```json
{
  "id": "355d7aeb-00cc-47d2-baa2-8f2fe4c2bf0d",
  "name": "Mac内置摄像头",
  "source": "0",
  "type": "mac_camera",
  "enabled": true,
  "fps": 1.0,
  "resolution": 640,
  "status": "stopped",
  "last_error": null
}
```
