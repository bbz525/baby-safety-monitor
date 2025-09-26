package repository

import (
	"baby-safety-monitor/internal/database"
	"baby-safety-monitor/internal/models"
	"time"

	"gorm.io/gorm"
)

type AlertRepository struct {
	db *gorm.DB
}

func NewAlertRepository() *AlertRepository {
	return &AlertRepository{
		db: database.GetDB(),
	}
}

// Create 创建告警
func (r *AlertRepository) Create(alert *models.Alert) error {
	return r.db.Create(alert).Error
}

// FindRecentSince 查找指定时间之后的告警
func (r *AlertRepository) FindRecentSince(since time.Time) ([]models.Alert, error) {
	var alerts []models.Alert
	err := r.db.Where("timestamp >= ?", since).
		Order("timestamp DESC").
		Find(&alerts).Error
	return alerts, err
}

// FindByLevel 根据级别查找告警
func (r *AlertRepository) FindByLevel(level string) ([]models.Alert, error) {
	var alerts []models.Alert
	err := r.db.Where("level = ?", level).
		Order("timestamp DESC").
		Find(&alerts).Error
	return alerts, err
}

// Count 统计告警数量
func (r *AlertRepository) Count() (int64, error) {
	var count int64
	err := r.db.Model(&models.Alert{}).Count(&count).Error
	return count, err
}

// DeleteOldAlerts 删除旧告警
func (r *AlertRepository) DeleteOldAlerts(before time.Time) error {
	return r.db.Where("timestamp < ?", before).Delete(&models.Alert{}).Error
}
