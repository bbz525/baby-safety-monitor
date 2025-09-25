#!/usr/bin/env python3
"""
Mac摄像头简单接入方案
使用系统命令获取权限并测试摄像头
"""

import subprocess
import cv2
import requests
import time
import json

VISION_BASE = "http://localhost:8001"

def request_camera_permission():
    """请求摄像头权限"""
    print("🔐 请求Mac摄像头权限...")
    
    # 使用系统命令打开摄像头应用来触发权限请求
    try:
        # 尝试打开Photo Booth来触发权限请求
        subprocess.run(["open", "-a", "Photo Booth"], check=True, timeout=5)
        print("✅ 已打开Photo Booth，请在弹出窗口中授权摄像头权限")
        print("💡 授权后请关闭Photo Booth，然后按回车继续...")
        input()
    except Exception as e:
        print(f"⚠️ 无法自动打开Photo Booth: {e}")
        print("💡 请手动打开任何使用摄像头的应用（如Photo Booth、FaceTime等）来授权权限")

def test_camera_access():
    """测试摄像头访问"""
    print("🔍 测试摄像头访问...")
    
    cap = None
    try:
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("❌ 摄像头无法打开")
            return False
        
        print("✅ 摄像头打开成功")
        
        # 尝试读取一帧
        ret, frame = cap.read()
        if not ret or frame is None:
            print("❌ 无法读取视频帧")
            return False
        
        print(f"✅ 成功读取视频帧: {frame.shape[1]}x{frame.shape[0]}")
        
        # 保存一帧作为测试
        cv2.imwrite("/tmp/mac_camera_test.jpg", frame)
        print("✅ 已保存测试图片到 /tmp/mac_camera_test.jpg")
        
        return True
        
    except Exception as e:
        print(f"❌ 摄像头测试失败: {e}")
        return False
    finally:
        if cap:
            cap.release()

def add_mac_camera_to_vision():
    """添加Mac摄像头到Vision服务"""
    print("📹 添加Mac摄像头到Vision服务...")
    
    camera_config = {
        "name": "Mac内置摄像头",
        "source": "0",  # 使用索引0
        "type": "mac_camera",
        "fps": 1.0,
        "resolution": 640,
        "enabled": True
    }
    
    try:
        response = requests.post(f"{VISION_BASE}/cameras", json=camera_config)
        response.raise_for_status()
        result = response.json()
        print(f"✅ 摄像头已添加: {result['id']}")
        return result['id']
    except Exception as e:
        print(f"❌ 添加摄像头失败: {e}")
        return None

def start_camera(camera_id):
    """启动摄像头"""
    print("🚀 启动摄像头...")
    
    try:
        response = requests.post(f"{VISION_BASE}/cameras/{camera_id}/start")
        response.raise_for_status()
        result = response.json()
        
        if result.get('started'):
            print("✅ 摄像头启动成功")
            return True
        else:
            print("❌ 摄像头启动失败")
            return False
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return False

def monitor_camera(camera_id, duration=10):
    """监控摄像头状态"""
    print(f"📊 监控摄像头状态 {duration} 秒...")
    
    for i in range(duration):
        try:
            response = requests.get(f"{VISION_BASE}/cameras/{camera_id}")
            response.raise_for_status()
            camera = response.json()
            
            status = camera['status']
            error = camera.get('last_error', '')
            
            print(f"  [{i+1:2d}s] 状态: {status}", end="")
            if error:
                print(f" | 错误: {error}")
            else:
                print()
                
        except Exception as e:
            print(f"  [{i+1:2d}s] 获取状态失败: {e}")
        
        time.sleep(1)

def main():
    print("=== Mac摄像头接入方案 ===\n")
    
    # 检查Vision服务
    try:
        response = requests.get(f"{VISION_BASE}/health")
        print(f"✅ Vision服务运行正常")
    except Exception as e:
        print(f"❌ Vision服务未运行: {e}")
        print("请先启动Vision服务: uvicorn app:app --host 0.0.0.0 --port 8001")
        return
    
    # 请求权限
    request_camera_permission()
    
    # 测试摄像头
    if not test_camera_access():
        print("\n❌ 摄像头测试失败，请检查权限设置")
        print("💡 解决方案:")
        print("1. 打开 系统偏好设置 > 安全性与隐私 > 隐私 > 摄像头")
        print("2. 确保终端或Python应用有摄像头权限")
        print("3. 重启终端后重试")
        return
    
    # 添加到Vision服务
    camera_id = add_mac_camera_to_vision()
    if not camera_id:
        return
    
    # 启动摄像头
    if start_camera(camera_id):
        # 监控状态
        monitor_camera(camera_id, 5)
        
        print(f"\n🎉 Mac摄像头设置完成！")
        print(f"摄像头ID: {camera_id}")
        print(f"\n管理命令:")
        print(f"  查看状态: curl http://localhost:8001/cameras/{camera_id}")
        print(f"  停止摄像头: curl -X POST http://localhost:8001/cameras/{camera_id}/stop")
        print(f"  删除摄像头: curl -X DELETE http://localhost:8001/cameras/{camera_id}")
    else:
        print("❌ 摄像头启动失败")

if __name__ == "__main__":
    main()
