#!/usr/bin/env python3
"""
Mac摄像头接入设置脚本
使用OpenCV访问Mac内置摄像头
"""

import cv2
import requests
import time
import json
from typing import Optional

VISION_BASE = "http://localhost:8001"


def test_mac_camera() -> Optional[int]:
    """测试Mac摄像头并返回可用的摄像头索引"""
    print("🔍 检测Mac摄像头...")
    
    # 尝试不同的摄像头索引
    for i in range(5):
        print(f"  测试摄像头索引 {i}...")
        cap = cv2.VideoCapture(i)
        
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                print(f"✅ 找到可用摄像头: 索引 {i}")
                print(f"   分辨率: {frame.shape[1]}x{frame.shape[0]}")
                cap.release()
                return i
            cap.release()
        else:
            cap.release()
    
    print("❌ 未找到可用的Mac摄像头")
    return None


def create_mac_camera_config(camera_index: int) -> dict:
    """创建Mac摄像头配置"""
    return {
        "name": f"Mac摄像头 (索引{camera_index})",
        "source": str(camera_index),  # OpenCV使用数字索引
        "type": "mac_camera",  # 自定义类型
        "fps": 1.0,
        "resolution": 640,
        "enabled": True
    }


def add_mac_camera_to_vision(camera_config: dict) -> Optional[str]:
    """将Mac摄像头添加到Vision服务"""
    try:
        response = requests.post(f"{VISION_BASE}/cameras", json=camera_config)
        response.raise_for_status()
        result = response.json()
        print(f"✅ 摄像头已添加到Vision服务: {result['id']}")
        return result['id']
    except Exception as e:
        print(f"❌ 添加摄像头失败: {e}")
        return None


def start_mac_camera(camera_id: str) -> bool:
    """启动Mac摄像头"""
    try:
        response = requests.post(f"{VISION_BASE}/cameras/{camera_id}/start")
        response.raise_for_status()
        result = response.json()
        if result.get('started'):
            print("✅ Mac摄像头启动成功")
            return True
        else:
            print("❌ Mac摄像头启动失败")
            return False
    except Exception as e:
        print(f"❌ 启动摄像头失败: {e}")
        return False


def monitor_camera_status(camera_id: str, duration: int = 10):
    """监控摄像头状态"""
    print(f"📹 监控摄像头状态，持续 {duration} 秒...")
    
    for i in range(duration):
        try:
            response = requests.get(f"{VISION_BASE}/cameras/{camera_id}")
            response.raise_for_status()
            camera = response.json()
            
            status = camera['status']
            error = camera.get('last_error')
            
            print(f"  [{i+1:2d}s] 状态: {status}", end="")
            if error:
                print(f" | 错误: {error}")
            else:
                print()
                
        except Exception as e:
            print(f"  [{i+1:2d}s] 获取状态失败: {e}")
        
        time.sleep(1)


def main():
    print("=== Mac摄像头接入设置 ===\n")
    
    # 检查Vision服务
    try:
        response = requests.get(f"{VISION_BASE}/health")
        print(f"✅ Vision服务运行正常: {response.json()}")
    except Exception as e:
        print(f"❌ Vision服务未运行: {e}")
        print("请先启动Vision服务: uvicorn app:app --host 0.0.0.0 --port 8001")
        return
    
    # 检测Mac摄像头
    camera_index = test_mac_camera()
    if camera_index is None:
        print("\n💡 提示:")
        print("1. 确保摄像头没有被其他应用占用")
        print("2. 检查系统权限设置")
        print("3. 尝试重启终端或重新插拔外接摄像头")
        return
    
    # 创建摄像头配置
    camera_config = create_mac_camera_config(camera_index)
    print(f"\n📋 摄像头配置:")
    print(json.dumps(camera_config, indent=2, ensure_ascii=False))
    
    # 添加到Vision服务
    camera_id = add_mac_camera_to_vision(camera_config)
    if not camera_id:
        return
    
    # 启动摄像头
    if start_mac_camera(camera_id):
        # 监控状态
        monitor_camera_status(camera_id, 5)
        
        print(f"\n🎉 Mac摄像头设置完成！")
        print(f"摄像头ID: {camera_id}")
        print(f"管理命令:")
        print(f"  查看状态: curl http://localhost:8001/cameras/{camera_id}")
        print(f"  停止摄像头: curl -X POST http://localhost:8001/cameras/{camera_id}/stop")
        print(f"  删除摄像头: curl -X DELETE http://localhost:8001/cameras/{camera_id}")
    else:
        print("❌ 摄像头启动失败")


if __name__ == "__main__":
    main()
