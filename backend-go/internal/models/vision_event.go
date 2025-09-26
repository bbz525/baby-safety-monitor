package models

import (
	"time"
)

// VisionEvent 视觉事件模型
type VisionEvent struct {
	ID        uint      `json:"id" gorm:"primaryKey"`
	Timestamp time.Time `json:"timestamp" gorm:"column:ts;not null;index:idx_vision_event_ts_track"`
	TrackID   string    `json:"trackId" gorm:"column:track_id;not null;index:idx_vision_event_ts_track"`
	X         int       `json:"x" gorm:"not null"`
	Y         int       `json:"y" gorm:"not null"`
	W         int       `json:"w" gorm:"not null"`
	H         int       `json:"h" gorm:"not null"`
	Action    string    `json:"action"`
	RiskScore float64   `json:"riskScore" gorm:"column:risk_score"`
	CreatedAt time.Time `json:"createdAt"`
	UpdatedAt time.Time `json:"updatedAt"`
}

// TableName 指定表名
func (VisionEvent) TableName() string {
	return "vision_event"
}

// VisionEventRequest 视觉事件请求
type VisionEventRequest struct {
	Timestamp string  `json:"timestamp"`
	TrackID   string  `json:"trackId" binding:"required"`
	Bbox      []int   `json:"bbox" binding:"required"`
	Action    string  `json:"action"`
	RiskScore float64 `json:"riskScore"`
}

// ToVisionEvent 转换为VisionEvent
func (req *VisionEventRequest) ToVisionEvent() *VisionEvent {
	event := &VisionEvent{
		TrackID:   req.TrackID,
		Action:    req.Action,
		RiskScore: req.RiskScore,
	}

	// 解析时间戳
	if req.Timestamp != "" {
		if t, err := time.Parse(time.RFC3339, req.Timestamp); err == nil {
			event.Timestamp = t
		} else {
			event.Timestamp = time.Now()
		}
	} else {
		event.Timestamp = time.Now()
	}

	// 解析边界框
	if len(req.Bbox) >= 4 {
		event.X = req.Bbox[0]
		event.Y = req.Bbox[1]
		event.W = req.Bbox[2]
		event.H = req.Bbox[3]
	}

	return event
}
