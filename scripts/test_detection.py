#!/usr/bin/env python3
"""
检测测试脚本
验证Mac摄像头是否正在检测人员
"""

import cv2
import time
from ultralytics import YOLO

def test_detection():
    """测试人员检测"""
    print("🔍 测试Mac摄像头人员检测...")
    
    # 加载YOLO模型
    print("📦 加载YOLO模型...")
    model = YOLO("yolov8n.pt")
    
    # 打开摄像头
    print("📹 打开Mac摄像头...")
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ 无法打开摄像头")
        return
    
    print("✅ 摄像头打开成功")
    
    # 设置分辨率
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 640)
    
    print("🎯 开始检测人员（按 'q' 退出）...")
    
    detection_count = 0
    
    try:
        for i in range(50):  # 检测50帧
            ret, frame = cap.read()
            if not ret:
                print("❌ 无法读取帧")
                break
            
            # 执行YOLO推理
            results = model.predict(
                source=frame,
                imgsz=640,
                conf=0.25,
                verbose=False
            )
            
            if results and results[0].boxes is not None:
                # 检查是否有人员检测
                persons = []
                for box in results[0].boxes:
                    cls_id = int(box.cls.item()) if box.cls is not None else -1
                    if cls_id == 0:  # COCO person class
                        conf = float(box.conf.item()) if box.conf is not None else 0.0
                        persons.append(conf)
                
                if persons:
                    max_conf = max(persons)
                    detection_count += 1
                    print(f"帧 {i+1:2d}: 检测到 {len(persons)} 个人员，最高置信度: {max_conf:.2f}")
                else:
                    print(f"帧 {i+1:2d}: 未检测到人员")
            else:
                print(f"帧 {i+1:2d}: 无检测结果")
            
            # 短暂延迟
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\n⏹️ 检测已停止")
    
    cap.release()
    
    print(f"\n📊 检测统计:")
    print(f"  总帧数: 50")
    print(f"  检测到人员的帧数: {detection_count}")
    print(f"  检测率: {detection_count/50*100:.1f}%")
    
    if detection_count > 0:
        print("✅ Mac摄像头人员检测正常工作！")
    else:
        print("⚠️ 未检测到人员，请检查:")
        print("  1. 摄像头前是否有人员")
        print("  2. 光线是否充足")
        print("  3. 摄像头角度是否合适")

if __name__ == "__main__":
    test_detection()
