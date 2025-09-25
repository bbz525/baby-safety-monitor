# Mac摄像头远程访问指南

## 🚀 三种远程访问方案

### 方案1: RTSP流服务器（推荐）

**特点**: 标准RTSP协议，兼容性好，延迟低

**启动**:
```bash
python scripts/rtsp_server.py
```

**访问地址**:
- 本地: `rtsp://localhost:8554/mac_camera`
- 远程: `rtsp://你的IP:8554/mac_camera`

**优点**:
- 标准RTSP协议
- 低延迟
- 支持VLC、FFplay等播放器
- 可以集成到其他系统

**缺点**:
- 需要安装FFmpeg
- 配置相对复杂

### 方案2: HTTP流服务器

**特点**: 简单易用，支持Web浏览器直接访问

**启动**:
```bash
python scripts/http_stream_server.py
```

**访问地址**:
- 本地: `http://localhost:8080`
- 远程: `http://你的IP:8080`

**优点**:
- 无需额外软件
- 支持Web浏览器
- 提供API接口
- 配置简单

**缺点**:
- 延迟较高
- 带宽消耗大

### 方案3: 集成Vision服务

**特点**: 功能完整，支持检测和管理

**启动**:
```bash
cd services/vision
python remote_vision.py
```

**访问地址**:
- 本地: `http://localhost:8005`
- 远程: `http://你的IP:8005`

**优点**:
- 功能完整
- 支持多摄像头
- 提供管理界面
- 支持检测功能

**缺点**:
- 资源消耗较大
- 配置复杂

## 🔧 快速开始

### 1. 获取本机IP地址
```bash
# 方法1: 使用脚本
python -c "import socket; s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(('8.8.8.8', 80)); print(s.getsockname()[0]); s.close()"

# 方法2: 系统命令
ifconfig | grep "inet " | grep -v 127.0.0.1
```

### 2. 启动远程服务

**推荐使用HTTP流服务器**:
```bash
python scripts/http_stream_server.py
```

### 3. 访问摄像头

**在浏览器中打开**:
```
http://你的IP地址:8080
```

**在手机/平板中打开**:
```
http://你的IP地址:8080
```

## 📱 移动设备访问

### iPhone/iPad
1. 确保设备与Mac在同一WiFi网络
2. 打开Safari浏览器
3. 输入 `http://你的IP:8080`
4. 即可查看摄像头画面

### Android设备
1. 确保设备与Mac在同一WiFi网络
2. 打开Chrome浏览器
3. 输入 `http://你的IP:8080`
4. 即可查看摄像头画面

## 🌐 外网访问

### 使用ngrok（推荐）

1. **安装ngrok**:
   ```bash
   brew install ngrok
   ```

2. **启动摄像头服务**:
   ```bash
   python scripts/http_stream_server.py
   ```

3. **在另一个终端启动ngrok**:
   ```bash
   ngrok http 8080
   ```

4. **获取公网地址**:
   ngrok会显示类似 `https://abc123.ngrok.io` 的地址

5. **访问**:
   在任何地方打开 `https://abc123.ngrok.io` 即可访问

### 使用路由器端口转发

1. **配置路由器**:
   - 登录路由器管理界面
   - 设置端口转发: 外网端口8080 → 内网IP:8080

2. **获取公网IP**:
   - 查看路由器WAN口IP
   - 或使用 `curl ifconfig.me`

3. **访问**:
   `http://公网IP:8080`

## 🔒 安全设置

### 1. 设置访问密码
修改HTTP流服务器，添加基本认证：

```python
# 在http_stream_server.py中添加
import base64

def check_auth(self):
    auth_header = self.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Basic '):
        return False
    
    credentials = base64.b64decode(auth_header[6:]).decode('utf-8')
    username, password = credentials.split(':', 1)
    return username == 'admin' and password == 'password'
```

### 2. 限制访问IP
```python
# 只允许特定IP访问
ALLOWED_IPS = ['192.168.1.100', '192.168.1.101']

def check_ip(self):
    client_ip = self.client_address[0]
    return client_ip in ALLOWED_IPS
```

### 3. 使用HTTPS
```bash
# 使用自签名证书
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
```

## 📊 性能优化

### 1. 调整视频参数
```python
# 降低分辨率和帧率
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 320)   # 降低分辨率
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
camera.set(cv2.CAP_PROP_FPS, 15)            # 降低帧率
```

### 2. 调整编码质量
```python
# 降低JPEG质量
cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
```

### 3. 使用硬件加速
```bash
# 安装支持硬件加速的FFmpeg
brew install ffmpeg --with-x264 --with-x265
```

## 🔍 故障排除

### 问题1: 无法访问摄像头
**解决方案**:
1. 检查防火墙设置
2. 确保端口未被占用
3. 检查摄像头权限

### 问题2: 视频延迟高
**解决方案**:
1. 降低分辨率和帧率
2. 使用有线网络连接
3. 关闭其他网络应用

### 问题3: 移动设备无法访问
**解决方案**:
1. 确保设备在同一网络
2. 检查路由器设置
3. 尝试使用IP地址而非域名

## 📝 使用示例

### 添加Mac摄像头到Vision服务
```bash
# 启动远程Vision服务
cd services/vision
python remote_vision.py

# 添加摄像头
curl -X POST http://localhost:8005/cameras \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mac摄像头",
    "source": "0",
    "type": "mac_camera",
    "fps": 1.0,
    "resolution": 640
  }'

# 启动摄像头
curl -X POST http://localhost:8005/cameras/{camera_id}/start
```

### 获取摄像头帧数据
```bash
# 获取单帧（JSON格式）
curl http://localhost:8005/api/cameras/{camera_id}/frame

# 获取视频流
curl http://localhost:8005/stream/{camera_id}
```

## 🎯 推荐配置

**家庭使用**:
- 方案: HTTP流服务器
- 分辨率: 640x480
- 帧率: 15 FPS
- 端口: 8080

**专业使用**:
- 方案: RTSP流服务器
- 分辨率: 1280x720
- 帧率: 30 FPS
- 端口: 8554

**开发测试**:
- 方案: 集成Vision服务
- 分辨率: 320x240
- 帧率: 1 FPS
- 端口: 8005
