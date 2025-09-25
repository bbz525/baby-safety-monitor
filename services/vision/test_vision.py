import pytest
import tempfile
import os
from fastapi.testclient import TestClient
from app import app, CameraConfig, CameraType, CameraStatus

client = TestClient(app)


def test_health():
    """测试健康检查接口"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_simulate_event():
    """测试模拟事件接口"""
    response = client.post("/simulate", params={
        "track_id": "test-1",
        "x": 100,
        "y": 120,
        "w": 60,
        "h": 80,
        "action": "walk",
        "risk": 0.5
    })
    assert response.status_code == 200
    data = response.json()
    assert data["sent"] is True


def test_camera_crud():
    """测试摄像头CRUD操作"""
    # 创建摄像头
    camera_data = {
        "id": "test-camera-1",
        "name": "测试摄像头",
        "source": "rtsp://test.example.com/stream",
        "type": "rtsp",
        "enabled": True,
        "fps": 1.0,
        "resolution": 640
    }
    
    response = client.post("/cameras", json=camera_data)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "test-camera-1"
    assert data["name"] == "测试摄像头"
    assert data["status"] == CameraStatus.STOPPED
    
    # 获取摄像头列表
    response = client.get("/cameras")
    assert response.status_code == 200
    cameras = response.json()
    assert len(cameras) == 1
    assert cameras[0]["id"] == "test-camera-1"
    
    # 获取单个摄像头
    response = client.get("/cameras/test-camera-1")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "测试摄像头"
    
    # 更新摄像头
    update_data = {
        "id": "test-camera-1",
        "name": "更新后的摄像头",
        "source": "rtsp://test.example.com/stream2",
        "type": "rtsp",
        "enabled": False,
        "fps": 2.0,
        "resolution": 1280
    }
    response = client.put("/cameras/test-camera-1", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "更新后的摄像头"
    assert data["fps"] == 2.0
    
    # 删除摄像头
    response = client.delete("/cameras/test-camera-1")
    assert response.status_code == 200
    data = response.json()
    assert data["deleted"] is True
    
    # 验证删除
    response = client.get("/cameras/test-camera-1")
    assert response.status_code == 404


def test_camera_operations():
    """测试摄像头启动/停止操作"""
    # 先创建摄像头
    camera_data = {
        "id": "test-camera-2",
        "name": "操作测试摄像头",
        "source": "rtsp://test.example.com/stream",
        "type": "rtsp",
        "enabled": True,
        "fps": 1.0,
        "resolution": 640
    }
    
    response = client.post("/cameras", json=camera_data)
    assert response.status_code == 200
    
    # 测试启动（会失败因为RTSP源不存在，但接口应该正常响应）
    response = client.post("/cameras/test-camera-2/start")
    assert response.status_code == 200
    data = response.json()
    assert data["started"] is True
    
    # 测试停止
    response = client.post("/cameras/test-camera-2/stop")
    assert response.status_code == 200
    data = response.json()
    assert data["stopped"] is True
    
    # 清理
    client.delete("/cameras/test-camera-2")


def test_infer_with_file():
    """测试文件推理接口"""
    # 创建一个测试图片文件
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
        # 写入一个简单的JPEG头部（最小有效JPEG）
        jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9'
        tmp_file.write(jpeg_header)
        tmp_file.flush()
        
        # 测试文件上传推理
        with open(tmp_file.name, 'rb') as f:
            response = client.post("/infer", files={"file": f})
        
        # 清理临时文件
        os.unlink(tmp_file.name)
    
    # 由于是无效图片，应该返回错误或空检测结果
    assert response.status_code == 200
    data = response.json()
    assert "detections" in data


def test_infer_with_url():
    """测试URL推理接口"""
    response = client.post("/infer", data={
        "source_url": "https://ultralytics.com/images/bus.jpg",
        "track_id": "test-track"
    })
    
    # 由于需要网络访问，可能成功或失败
    assert response.status_code == 200
    data = response.json()
    # 应该包含detections字段
    assert "detections" in data


def test_last_frame():
    """测试最后帧接口"""
    response = client.get("/last.jpg")
    # 可能返回图片或错误，但接口应该正常响应
    assert response.status_code in [200, 404]


def test_camera_validation():
    """测试摄像头数据验证"""
    # 测试无效的摄像头类型
    invalid_camera = {
        "id": "invalid-camera",
        "name": "无效摄像头",
        "source": "invalid://test",
        "type": "invalid_type",
        "enabled": True,
        "fps": 1.0,
        "resolution": 640
    }
    
    response = client.post("/cameras", json=invalid_camera)
    # 应该返回422验证错误
    assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
