package models

import (
	"time"
)

// Alert 告警模型
type Alert struct {
	ID          uint      `json:"id" gorm:"primaryKey"`
	Timestamp   time.Time `json:"timestamp" gorm:"not null;index"`
	TrackID     string    `json:"trackId" gorm:"column:track_id;not null;index"`
	ZoneID      *uint     `json:"zoneId" gorm:"column:zone_id"`
	Level       string    `json:"level" gorm:"not null"`
	Reason      string    `json:"reason" gorm:"not null"`
	DetailsJSON string    `json:"detailsJson" gorm:"column:details_json;type:text"`
	CreatedAt   time.Time `json:"createdAt"`
	UpdatedAt   time.Time `json:"updatedAt"`
}

// TableName 指定表名
func (Alert) TableName() string {
	return "alert"
}

// AlertRequest 告警请求
type AlertRequest struct {
	Timestamp   string `json:"timestamp"`
	TrackID     string `json:"trackId" binding:"required"`
	ZoneID      *uint  `json:"zoneId"`
	Level       string `json:"level" binding:"required"`
	Reason      string `json:"reason" binding:"required"`
	DetailsJSON string `json:"detailsJson"`
}

// ToAlert 转换为Alert
func (req *AlertRequest) ToAlert() *Alert {
	alert := &Alert{
		TrackID:     req.TrackID,
		ZoneID:      req.ZoneID,
		Level:       req.Level,
		Reason:      req.Reason,
		DetailsJSON: req.DetailsJSON,
	}

	// 解析时间戳
	if req.Timestamp != "" {
		if t, err := time.Parse(time.RFC3339, req.Timestamp); err == nil {
			alert.Timestamp = t
		} else {
			alert.Timestamp = time.Now()
		}
	} else {
		alert.Timestamp = time.Now()
	}

	return alert
}
