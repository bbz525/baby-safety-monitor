#!/usr/bin/env python3
"""
Mac摄像头权限测试脚本
"""

import cv2
import time

def test_camera_with_permission():
    """测试摄像头权限"""
    print("🔍 测试Mac摄像头权限...")
    
    # 尝试访问摄像头
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ 无法打开摄像头")
        print("💡 可能的原因:")
        print("1. 摄像头被其他应用占用")
        print("2. 系统权限未授权")
        print("3. 需要重启终端")
        return False
    
    print("✅ 摄像头打开成功")
    
    # 尝试读取一帧
    ret, frame = cap.read()
    if not ret:
        print("❌ 无法读取视频帧")
        cap.release()
        return False
    
    print(f"✅ 成功读取视频帧: {frame.shape}")
    
    # 显示几帧
    print("📹 显示视频流 (按 'q' 退出)...")
    for i in range(30):  # 显示3秒
        ret, frame = cap.read()
        if not ret:
            print("❌ 读取帧失败")
            break
        
        # 显示帧信息
        print(f"帧 {i+1}: {frame.shape}", end='\r')
        
        # 等待
        time.sleep(0.1)
    
    cap.release()
    print("\n✅ 摄像头测试完成")
    return True

if __name__ == "__main__":
    test_camera_with_permission()
