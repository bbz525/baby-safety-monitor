package controller

import (
	"baby-safety-monitor/internal/models"
	"baby-safety-monitor/internal/repository"
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
	"github.com/sirupsen/logrus"
)

type DangerZoneController struct {
	dangerZoneRepo *repository.DangerZoneRepository
}

func NewDangerZoneController() *DangerZoneController {
	return &DangerZoneController{
		dangerZoneRepo: repository.NewDangerZoneRepository(),
	}
}

// CreateDangerZone 创建危险区域
func (c *DangerZoneController) CreateDangerZone(ctx *gin.Context) {
	var req models.DangerZoneRequest
	if err := ctx.ShouldBindJSON(&req); err != nil {
		ctx.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// 转换为DangerZone
	zone := req.ToDangerZone()

	// 保存到数据库
	if err := c.dangerZoneRepo.Create(zone); err != nil {
		logrus.Errorf("保存危险区域失败: %v", err)
		ctx.JSON(http.StatusInternalServerError, gin.H{"error": "保存区域失败"})
		return
	}

	logrus.Infof("危险区域已创建: Name=%s, Level=%s", zone.Name, zone.Level)

	ctx.JSON(http.StatusCreated, gin.H{
		"message": "危险区域创建成功",
		"zone":    zone,
	})
}

// GetDangerZones 获取所有危险区域
func (c *DangerZoneController) GetDangerZones(ctx *gin.Context) {
	zones, err := c.dangerZoneRepo.FindAll()
	if err != nil {
		logrus.Errorf("查询危险区域失败: %v", err)
		ctx.JSON(http.StatusInternalServerError, gin.H{"error": "查询区域失败"})
		return
	}

	ctx.JSON(http.StatusOK, zones)
}

// GetDangerZone 获取指定危险区域
func (c *DangerZoneController) GetDangerZone(ctx *gin.Context) {
	idStr := ctx.Param("id")
	id, err := strconv.ParseUint(idStr, 10, 32)
	if err != nil {
		ctx.JSON(http.StatusBadRequest, gin.H{"error": "无效的ID"})
		return
	}

	zone, err := c.dangerZoneRepo.FindByID(uint(id))
	if err != nil {
		ctx.JSON(http.StatusNotFound, gin.H{"error": "危险区域不存在"})
		return
	}

	ctx.JSON(http.StatusOK, zone)
}

// UpdateDangerZone 更新危险区域
func (c *DangerZoneController) UpdateDangerZone(ctx *gin.Context) {
	idStr := ctx.Param("id")
	id, err := strconv.ParseUint(idStr, 10, 32)
	if err != nil {
		ctx.JSON(http.StatusBadRequest, gin.H{"error": "无效的ID"})
		return
	}

	// 查找现有区域
	zone, err := c.dangerZoneRepo.FindByID(uint(id))
	if err != nil {
		ctx.JSON(http.StatusNotFound, gin.H{"error": "危险区域不存在"})
		return
	}

	// 绑定更新数据
	var req models.DangerZoneRequest
	if err := ctx.ShouldBindJSON(&req); err != nil {
		ctx.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// 更新字段
	zone.Name = req.Name
	zone.PolygonJSON = req.PolygonJSON
	zone.Level = req.Level
	zone.Enabled = req.Enabled

	// 保存更新
	if err := c.dangerZoneRepo.Update(zone); err != nil {
		logrus.Errorf("更新危险区域失败: %v", err)
		ctx.JSON(http.StatusInternalServerError, gin.H{"error": "更新区域失败"})
		return
	}

	logrus.Infof("危险区域已更新: ID=%d, Name=%s", zone.ID, zone.Name)

	ctx.JSON(http.StatusOK, gin.H{
		"message": "危险区域更新成功",
		"zone":    zone,
	})
}

// DeleteDangerZone 删除危险区域
func (c *DangerZoneController) DeleteDangerZone(ctx *gin.Context) {
	idStr := ctx.Param("id")
	id, err := strconv.ParseUint(idStr, 10, 32)
	if err != nil {
		ctx.JSON(http.StatusBadRequest, gin.H{"error": "无效的ID"})
		return
	}

	// 检查区域是否存在
	_, err = c.dangerZoneRepo.FindByID(uint(id))
	if err != nil {
		ctx.JSON(http.StatusNotFound, gin.H{"error": "危险区域不存在"})
		return
	}

	// 删除区域
	if err := c.dangerZoneRepo.Delete(uint(id)); err != nil {
		logrus.Errorf("删除危险区域失败: %v", err)
		ctx.JSON(http.StatusInternalServerError, gin.H{"error": "删除区域失败"})
		return
	}

	logrus.Infof("危险区域已删除: ID=%d", id)

	ctx.JSON(http.StatusOK, gin.H{
		"message": "危险区域删除成功",
	})
}

// GetEnabledDangerZones 获取启用的危险区域
func (c *DangerZoneController) GetEnabledDangerZones(ctx *gin.Context) {
	zones, err := c.dangerZoneRepo.FindEnabled()
	if err != nil {
		logrus.Errorf("查询启用的危险区域失败: %v", err)
		ctx.JSON(http.StatusInternalServerError, gin.H{"error": "查询区域失败"})
		return
	}

	ctx.JSON(http.StatusOK, zones)
}
