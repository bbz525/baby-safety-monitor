#!/usr/bin/env python3
"""
Mac摄像头HTTP流服务器
将Mac摄像头暴露为HTTP流，供远程访问
"""

import cv2
import threading
import time
import base64
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import io

class CameraStreamHandler(BaseHTTPRequestHandler):
    def __init__(self, camera, *args, **kwargs):
        self.camera = camera
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Mac摄像头流</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    .container { max-width: 800px; margin: 0 auto; }
                    .video { width: 100%; max-width: 640px; }
                    .info { background: #f0f0f0; padding: 10px; margin: 10px 0; border-radius: 5px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Mac摄像头实时流</h1>
                    <div class="info">
                        <p><strong>摄像头状态:</strong> <span id="status">连接中...</span></p>
                        <p><strong>分辨率:</strong> <span id="resolution">-</span></p>
                        <p><strong>帧率:</strong> <span id="fps">-</span></p>
                    </div>
                    <img id="video" class="video" src="/stream" alt="摄像头流">
                    <div class="info">
                        <p><strong>访问地址:</strong></p>
                        <ul>
                            <li>HTTP流: <code id="stream_url">-</code></li>
                            <li>JSON API: <code id="api_url">-</code></li>
                        </ul>
                    </div>
                </div>
                <script>
                    // 更新URL信息
                    document.getElementById('stream_url').textContent = window.location.origin + '/stream';
                    document.getElementById('api_url').textContent = window.location.origin + '/api';
                    
                    // 定期检查状态
                    setInterval(() => {
                        fetch('/api')
                            .then(response => response.json())
                            .then(data => {
                                document.getElementById('status').textContent = data.status;
                                document.getElementById('resolution').textContent = data.resolution;
                                document.getElementById('fps').textContent = data.fps;
                            })
                            .catch(err => {
                                document.getElementById('status').textContent = '连接失败';
                            });
                    }, 1000);
                </script>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
            
        elif self.path == '/stream':
            self.send_response(200)
            self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=frame')
            self.end_headers()
            
            while True:
                ret, frame = self.camera.read()
                if not ret:
                    break
                
                # 调整大小
                frame = cv2.resize(frame, (640, 480))
                
                # 编码为JPEG
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                
                # 发送帧
                self.wfile.write(b'--frame\r\n')
                self.send_header('Content-type', 'image/jpeg')
                self.send_header('Content-Length', str(len(buffer)))
                self.end_headers()
                self.wfile.write(buffer.tobytes())
                self.wfile.write(b'\r\n')
                
                time.sleep(0.033)  # ~30 FPS
                
        elif self.path == '/api':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            ret, frame = self.camera.read()
            if ret:
                status = "运行中"
                resolution = f"{frame.shape[1]}x{frame.shape[0]}"
            else:
                status = "错误"
                resolution = "未知"
            
            data = {
                "status": status,
                "resolution": resolution,
                "fps": "30",
                "timestamp": time.time()
            }
            
            self.wfile.write(json.dumps(data).encode())
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # 减少日志输出
        pass

class HTTPStreamServer:
    def __init__(self, camera_index: int = 0, port: int = 8081):
        self.camera_index = camera_index
        self.port = port
        self.camera = None
        self.server = None
        self.running = False
    
    def start(self):
        """启动HTTP流服务器"""
        print(f"🚀 启动Mac摄像头HTTP流服务器...")
        print(f"   摄像头索引: {self.camera_index}")
        print(f"   HTTP端口: {self.port}")
        
        # 打开摄像头
        self.camera = cv2.VideoCapture(self.camera_index)
        if not self.camera.isOpened():
            print(f"❌ 无法打开摄像头索引 {self.camera_index}")
            return False
        
        # 设置摄像头参数
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.camera.set(cv2.CAP_PROP_FPS, 30)
        
        print("✅ 摄像头打开成功")
        
        # 创建HTTP服务器
        handler = lambda *args, **kwargs: CameraStreamHandler(self.camera, *args, **kwargs)
        self.server = HTTPServer(('0.0.0.0', self.port), handler)
        
        self.running = True
        print(f"✅ HTTP流服务器启动成功!")
        print(f"🌐 访问地址: http://localhost:{self.port}")
        print(f"📺 视频流: http://localhost:{self.port}/stream")
        print(f"📊 API接口: http://localhost:{self.port}/api")
        print(f"⏹️  按 Ctrl+C 停止服务器")
        
        return True
    
    def run(self):
        """运行服务器"""
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """停止服务器"""
        print("\n⏹️  停止HTTP流服务器...")
        self.running = False
        
        if self.server:
            self.server.shutdown()
        
        if self.camera:
            self.camera.release()
        
        print("✅ HTTP流服务器已停止")

def get_local_ip() -> str:
    """获取本机IP地址"""
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

def main():
    print("=== Mac摄像头HTTP流服务器 ===\n")
    
    # 获取本机IP
    local_ip = get_local_ip()
    print(f"🌐 本机IP地址: {local_ip}")
    
    # 创建HTTP流服务器
    server = HTTPStreamServer(
        camera_index=0,  # Mac内置摄像头
        port=8081  # HTTP端口
    )
    
    # 启动服务器
    if not server.start():
        print("❌ 服务器启动失败")
        return
    
    # 显示访问信息
    print(f"\n📺 访问地址:")
    print(f"   本地: http://localhost:8081")
    print(f"   远程: http://{local_ip}:8081")
    print(f"\n💡 在其他设备上使用以下地址访问:")
    print(f"   http://{local_ip}:8081")
    print(f"   http://{local_ip}:8081/stream")
    
    # 运行服务器
    server.run()

if __name__ == "__main__":
    main()
