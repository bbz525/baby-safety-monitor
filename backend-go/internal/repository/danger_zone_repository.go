package repository

import (
	"baby-safety-monitor/internal/database"
	"baby-safety-monitor/internal/models"

	"gorm.io/gorm"
)

type DangerZoneRepository struct {
	db *gorm.DB
}

func NewDangerZoneRepository() *DangerZoneRepository {
	return &DangerZoneRepository{
		db: database.GetDB(),
	}
}

// Create 创建危险区域
func (r *DangerZoneRepository) Create(zone *models.DangerZone) error {
	return r.db.Create(zone).Error
}

// FindAll 查找所有危险区域
func (r *DangerZoneRepository) FindAll() ([]models.DangerZone, error) {
	var zones []models.DangerZone
	err := r.db.Find(&zones).Error
	return zones, err
}

// FindByID 根据ID查找危险区域
func (r *DangerZoneRepository) FindByID(id uint) (*models.DangerZone, error) {
	var zone models.DangerZone
	err := r.db.First(&zone, id).Error
	if err != nil {
		return nil, err
	}
	return &zone, nil
}

// Update 更新危险区域
func (r *DangerZoneRepository) Update(zone *models.DangerZone) error {
	return r.db.Save(zone).Error
}

// Delete 删除危险区域
func (r *DangerZoneRepository) Delete(id uint) error {
	return r.db.Delete(&models.DangerZone{}, id).Error
}

// FindEnabled 查找启用的危险区域
func (r *DangerZoneRepository) FindEnabled() ([]models.DangerZone, error) {
	var zones []models.DangerZone
	err := r.db.Where("enabled = ?", true).Find(&zones).Error
	return zones, err
}
