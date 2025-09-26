package repository

import (
	"baby-safety-monitor/internal/database"
	"baby-safety-monitor/internal/models"
	"time"

	"gorm.io/gorm"
)

type VisionEventRepository struct {
	db *gorm.DB
}

func NewVisionEventRepository() *VisionEventRepository {
	return &VisionEventRepository{
		db: database.GetDB(),
	}
}

// Create 创建视觉事件
func (r *VisionEventRepository) Create(event *models.VisionEvent) error {
	return r.db.Create(event).Error
}

// FindRecentSince 查找指定时间之后的事件
func (r *VisionEventRepository) FindRecentSince(since time.Time) ([]models.VisionEvent, error) {
	var events []models.VisionEvent
	err := r.db.Where("ts >= ?", since).
		Order("ts DESC").
		Find(&events).Error
	return events, err
}

// FindByTrackID 根据TrackID查找事件
func (r *VisionEventRepository) FindByTrackID(trackID string) ([]models.VisionEvent, error) {
	var events []models.VisionEvent
	err := r.db.Where("track_id = ?", trackID).
		Order("ts DESC").
		Find(&events).Error
	return events, err
}

// Count 统计事件数量
func (r *VisionEventRepository) Count() (int64, error) {
	var count int64
	err := r.db.Model(&models.VisionEvent{}).Count(&count).Error
	return count, err
}

// DeleteOldEvents 删除旧事件
func (r *VisionEventRepository) DeleteOldEvents(before time.Time) error {
	return r.db.Where("ts < ?", before).Delete(&models.VisionEvent{}).Error
}
