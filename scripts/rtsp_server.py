#!/usr/bin/env python3
"""
Mac摄像头RTSP服务器
将Mac摄像头暴露为RTSP流，供远程访问
"""

import cv2
import threading
import time
import subprocess
import os
import signal
import sys
from typing import Optional

class RTSPServer:
    def __init__(self, camera_index: int = 0, rtsp_port: int = 8554, stream_name: str = "mac_camera"):
        self.camera_index = camera_index
        self.rtsp_port = rtsp_port
        self.stream_name = stream_name
        self.cap = None
        self.ffmpeg_process = None
        self.running = False
        
    def start(self):
        """启动RTSP服务器"""
        print(f"🚀 启动Mac摄像头RTSP服务器...")
        print(f"   摄像头索引: {self.camera_index}")
        print(f"   RTSP端口: {self.rtsp_port}")
        print(f"   流名称: {self.stream_name}")
        
        # 测试摄像头
        if not self._test_camera():
            return False
        
        # 启动FFmpeg RTSP服务器
        if not self._start_ffmpeg():
            return False
        
        self.running = True
        print(f"✅ RTSP服务器启动成功!")
        print(f"📺 RTSP地址: rtsp://localhost:{self.rtsp_port}/{self.stream_name}")
        print(f"📺 远程访问: rtsp://你的IP地址:{self.rtsp_port}/{self.stream_name}")
        print(f"⏹️  按 Ctrl+C 停止服务器")
        
        return True
    
    def _test_camera(self) -> bool:
        """测试摄像头是否可用"""
        print("🔍 测试摄像头...")
        
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            print(f"❌ 无法打开摄像头索引 {self.camera_index}")
            return False
        
        ret, frame = self.cap.read()
        if not ret:
            print("❌ 无法读取摄像头帧")
            self.cap.release()
            return False
        
        print(f"✅ 摄像头测试成功: {frame.shape[1]}x{frame.shape[0]}")
        self.cap.release()
        return True
    
    def _start_ffmpeg(self) -> bool:
        """启动FFmpeg RTSP服务器"""
        print("📡 启动FFmpeg RTSP服务器...")
        
        # 检查FFmpeg是否安装
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ FFmpeg未安装，请先安装FFmpeg:")
            print("   brew install ffmpeg")
            return False
        
        # FFmpeg命令
        ffmpeg_cmd = [
            "ffmpeg",
            "-f", "avfoundation",  # macOS视频输入
            "-i", str(self.camera_index),  # 摄像头索引
            "-c:v", "libx264",  # 视频编码
            "-preset", "ultrafast",  # 编码速度
            "-tune", "zerolatency",  # 低延迟
            "-f", "rtsp",  # 输出格式
            f"rtsp://localhost:{self.rtsp_port}/{self.stream_name}"
        ]
        
        try:
            self.ffmpeg_process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # 等待一下看是否启动成功
            time.sleep(2)
            if self.ffmpeg_process.poll() is not None:
                stdout, stderr = self.ffmpeg_process.communicate()
                print(f"❌ FFmpeg启动失败:")
                print(f"   stdout: {stdout.decode()}")
                print(f"   stderr: {stderr.decode()}")
                return False
            
            print("✅ FFmpeg RTSP服务器启动成功")
            return True
            
        except Exception as e:
            print(f"❌ 启动FFmpeg失败: {e}")
            return False
    
    def stop(self):
        """停止RTSP服务器"""
        print("\n⏹️  停止RTSP服务器...")
        self.running = False
        
        if self.ffmpeg_process:
            self.ffmpeg_process.terminate()
            try:
                self.ffmpeg_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.ffmpeg_process.kill()
            print("✅ RTSP服务器已停止")
    
    def get_rtsp_url(self, local_ip: str = "localhost") -> str:
        """获取RTSP访问地址"""
        return f"rtsp://{local_ip}:{self.rtsp_port}/{self.stream_name}"

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
    print("=== Mac摄像头RTSP服务器 ===\n")
    
    # 获取本机IP
    local_ip = get_local_ip()
    print(f"🌐 本机IP地址: {local_ip}")
    
    # 创建RTSP服务器
    server = RTSPServer(
        camera_index=0,  # Mac内置摄像头
        rtsp_port=8554,  # RTSP端口
        stream_name="mac_camera"  # 流名称
    )
    
    # 设置信号处理
    def signal_handler(sig, frame):
        server.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # 启动服务器
    if not server.start():
        print("❌ 服务器启动失败")
        return
    
    # 显示访问信息
    print(f"\n📺 访问地址:")
    print(f"   本地: {server.get_rtsp_url()}")
    print(f"   远程: {server.get_rtsp_url(local_ip)}")
    print(f"\n💡 在其他设备上使用以下地址访问:")
    print(f"   rtsp://{local_ip}:8554/mac_camera")
    
    try:
        # 保持运行
        while server.running:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()

if __name__ == "__main__":
    main()
