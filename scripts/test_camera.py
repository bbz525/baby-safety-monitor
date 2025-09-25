#!/usr/bin/env python3
"""
摄像头连接测试脚本
测试指定的摄像头源是否可以正常连接
"""

import cv2
import sys
import time
from typing import Optional


def test_camera_source(source: str, timeout: int = 10) -> bool:
    """测试摄像头源是否可以连接"""
    print(f"测试摄像头源: {source}")
    
    cap = None
    try:
        # 创建VideoCapture对象
        cap = cv2.VideoCapture(source)
        
        if not cap.isOpened():
            print("❌ 无法打开摄像头源")
            return False
        
        # 设置超时
        start_time = time.time()
        
        # 尝试读取一帧
        ret, frame = cap.read()
        
        if not ret:
            print("❌ 无法读取视频帧")
            return False
        
        if frame is None or frame.size == 0:
            print("❌ 读取到空帧")
            return False
        
        print(f"✅ 摄像头连接成功")
        print(f"   分辨率: {frame.shape[1]}x{frame.shape[0]}")
        print(f"   通道数: {frame.shape[2] if len(frame.shape) > 2 else 1}")
        
        # 测试连续读取几帧
        print("测试连续读取...")
        for i in range(5):
            ret, frame = cap.read()
            if not ret:
                print(f"❌ 第{i+1}帧读取失败")
                return False
            print(f"   第{i+1}帧: {frame.shape}")
            time.sleep(0.1)
        
        print("✅ 连续读取测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中出现异常: {e}")
        return False
    finally:
        if cap:
            cap.release()


def main():
    if len(sys.argv) != 2:
        print("用法: python test_camera.py <camera_source>")
        print("示例:")
        print("  python test_camera.py rtsp://admin:password@192.168.1.100:554/stream")
        print("  python test_camera.py http://192.168.1.101:8080/video")
        print("  python test_camera.py /path/to/video.mp4")
        sys.exit(1)
    
    source = sys.argv[1]
    
    print("=== 摄像头连接测试 ===")
    print(f"源地址: {source}")
    print()
    
    success = test_camera_source(source)
    
    if success:
        print("\n🎉 摄像头测试成功！可以添加到监控系统中。")
        sys.exit(0)
    else:
        print("\n💥 摄像头测试失败！请检查源地址和网络连接。")
        sys.exit(1)


if __name__ == "__main__":
    main()
