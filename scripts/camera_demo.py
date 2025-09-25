#!/usr/bin/env python3
"""
摄像头接入演示脚本
演示如何添加、启动、监控和停止摄像头
"""

import requests
import time
import json
from typing import Dict, Any

VISION_BASE = "http://localhost:8001"


def create_camera(name: str, source: str, camera_type: str, fps: float = 1.0, resolution: int = 640) -> Dict[str, Any]:
    """创建摄像头"""
    data = {
        "name": name,
        "source": source,
        "type": camera_type,
        "fps": fps,
        "resolution": resolution
    }
    
    response = requests.post(f"{VISION_BASE}/cameras", json=data)
    response.raise_for_status()
    return response.json()


def list_cameras() -> list:
    """列出所有摄像头"""
    response = requests.get(f"{VISION_BASE}/cameras")
    response.raise_for_status()
    return response.json()


def get_camera(camera_id: str) -> Dict[str, Any]:
    """获取摄像头详情"""
    response = requests.get(f"{VISION_BASE}/cameras/{camera_id}")
    response.raise_for_status()
    return response.json()


def start_camera(camera_id: str) -> bool:
    """启动摄像头"""
    response = requests.post(f"{VISION_BASE}/cameras/{camera_id}/start")
    response.raise_for_status()
    return response.json()["started"]


def stop_camera(camera_id: str) -> bool:
    """停止摄像头"""
    response = requests.post(f"{VISION_BASE}/cameras/{camera_id}/stop")
    response.raise_for_status()
    return response.json()["stopped"]


def delete_camera(camera_id: str) -> bool:
    """删除摄像头"""
    response = requests.delete(f"{VISION_BASE}/cameras/{camera_id}")
    response.raise_for_status()
    return response.json()["deleted"]


def monitor_camera(camera_id: str, duration: int = 30):
    """监控摄像头状态"""
    print(f"监控摄像头 {camera_id} 状态，持续 {duration} 秒...")
    
    for i in range(duration):
        try:
            camera = get_camera(camera_id)
            status = camera["status"]
            error = camera.get("last_error")
            
            print(f"[{i+1:2d}s] 状态: {status}", end="")
            if error:
                print(f" | 错误: {error}")
            else:
                print()
                
        except Exception as e:
            print(f"[{i+1:2d}s] 获取状态失败: {e}")
        
        time.sleep(1)


def main():
    print("=== 摄像头接入演示 ===\n")
    
    # 检查Vision服务是否运行
    try:
        response = requests.get(f"{VISION_BASE}/health")
        print(f"✓ Vision服务运行正常: {response.json()}")
    except Exception as e:
        print(f"✗ Vision服务未运行: {e}")
        return
    
    print("\n1. 创建测试摄像头...")
    
    # 创建不同类型的摄像头
    cameras = []
    
    # RTSP摄像头（会失败，因为源不存在）
    rtsp_camera = create_camera(
        name="RTSP测试摄像头",
        source="rtsp://admin:password@192.168.1.100:554/stream1",
        camera_type="rtsp",
        fps=1.0,
        resolution=640
    )
    cameras.append(rtsp_camera)
    print(f"✓ 创建RTSP摄像头: {rtsp_camera['id']}")
    
    # HTTP摄像头（会失败，因为源不存在）
    http_camera = create_camera(
        name="HTTP测试摄像头", 
        source="http://192.168.1.101:8080/video",
        camera_type="http",
        fps=2.0,
        resolution=1280
    )
    cameras.append(http_camera)
    print(f"✓ 创建HTTP摄像头: {http_camera['id']}")
    
    # 本地文件摄像头（会失败，因为文件不存在）
    file_camera = create_camera(
        name="文件测试摄像头",
        source="/app/data/test_video.mp4",
        camera_type="file",
        fps=1.0,
        resolution=640
    )
    cameras.append(file_camera)
    print(f"✓ 创建文件摄像头: {file_camera['id']}")
    
    print(f"\n2. 当前摄像头列表:")
    for camera in list_cameras():
        print(f"  - {camera['name']} ({camera['type']}): {camera['status']}")
    
    print(f"\n3. 启动所有摄像头...")
    for camera in cameras:
        camera_id = camera["id"]
        try:
            if start_camera(camera_id):
                print(f"✓ 启动 {camera['name']} 成功")
            else:
                print(f"✗ 启动 {camera['name']} 失败")
        except Exception as e:
            print(f"✗ 启动 {camera['name']} 异常: {e}")
    
    print(f"\n4. 监控摄像头状态...")
    time.sleep(2)  # 等待摄像头尝试连接
    
    for camera in cameras:
        camera_id = camera["id"]
        camera_info = get_camera(camera_id)
        print(f"\n{camera_info['name']} 状态:")
        print(f"  状态: {camera_info['status']}")
        if camera_info.get('last_error'):
            print(f"  错误: {camera_info['last_error']}")
    
    print(f"\n5. 停止所有摄像头...")
    for camera in cameras:
        camera_id = camera["id"]
        try:
            if stop_camera(camera_id):
                print(f"✓ 停止 {camera['name']} 成功")
            else:
                print(f"✗ 停止 {camera['name']} 失败")
        except Exception as e:
            print(f"✗ 停止 {camera['name']} 异常: {e}")
    
    print(f"\n6. 清理摄像头...")
    for camera in cameras:
        camera_id = camera["id"]
        try:
            if delete_camera(camera_id):
                print(f"✓ 删除 {camera['name']} 成功")
            else:
                print(f"✗ 删除 {camera['name']} 失败")
        except Exception as e:
            print(f"✗ 删除 {camera['name']} 异常: {e}")
    
    print(f"\n=== 演示完成 ===")


if __name__ == "__main__":
    main()
