package models

import (
	"time"
)

// DangerZone 危险区域模型
type DangerZone struct {
	ID          uint      `json:"id" gorm:"primaryKey"`
	Name        string    `json:"name" gorm:"not null"`
	PolygonJSON string    `json:"polygonJson" gorm:"column:polygon_json;type:text;not null"`
	Level       string    `json:"level" gorm:"not null"`
	Enabled     bool      `json:"enabled" gorm:"default:true"`
	CreatedAt   time.Time `json:"createdAt"`
	UpdatedAt   time.Time `json:"updatedAt"`
}

// TableName 指定表名
func (DangerZone) TableName() string {
	return "danger_zone"
}

// DangerZoneRequest 危险区域请求
type DangerZoneRequest struct {
	Name        string `json:"name" binding:"required"`
	PolygonJSON string `json:"polygonJson" binding:"required"`
	Level       string `json:"level" binding:"required"`
	Enabled     bool   `json:"enabled"`
}

// ToDangerZone 转换为DangerZone
func (req *DangerZoneRequest) ToDangerZone() *DangerZone {
	return &DangerZone{
		Name:        req.Name,
		PolygonJSON: req.PolygonJSON,
		Level:       req.Level,
		Enabled:     req.Enabled,
	}
}
