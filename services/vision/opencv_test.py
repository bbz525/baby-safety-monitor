import cv2
import numpy as np

def access_camera():
    # 0 表示默认摄像头（通常是内置摄像头）
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("无法访问摄像头")
        return
    
    try:
        while True:
            # 读取帧
            ret, frame = cap.read()
            
            if not ret:
                print("无法读取帧")
                break
            print(frame)
            # 显示帧
            cv2.imshow('Mac Camera', frame)
            
            # 按 'q' 退出
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    finally:
        # 释放资源
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    access_camera()