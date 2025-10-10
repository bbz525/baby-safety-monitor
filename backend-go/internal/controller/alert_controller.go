package controller

import (
	"baby-safety-monitor/internal/models"
	"baby-safety-monitor/internal/repository"
	"baby-safety-monitor/internal/service"
	"net/http"
	"strconv"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/patrickmn/go-cache"
	"github.com/sirupsen/logrus"
)

type AlertController struct {
	alertRepo           *repository.AlertRepository
	notificationService *service.NotificationService
	sseHub              *service.SSEHub
	cache               *cache.Cache
}

func NewAlertController(sseHub *service.SSEHub) *AlertController {
	return &AlertController{
		alertRepo:           repository.NewAlertRepository(),
		notificationService: service.NewNotificationService(),
		sseHub:              sseHub,
		cache:               cache.New(5*time.Minute, 10*time.Minute),
	}
}

// CreateAlert 创建告警
func (c *AlertController) CreateAlert(ctx *gin.Context) {
	var req models.AlertRequest
	if err := ctx.ShouldBindJSON(&req); err != nil {
		ctx.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// 转换为Alert
	alert := req.ToAlert()

	// 保存到数据库
	if err := c.alertRepo.Create(alert); err != nil {
		logrus.Errorf("保存告警失败: %v", err)
		ctx.JSON(http.StatusInternalServerError, gin.H{"error": "保存告警失败"})
		return
	}

	// 发送钉钉通知
	if err := c.notificationService.SendDingtalkNotification(alert); err != nil {
		logrus.Errorf("发送钉钉通知失败: %v", err)
	}

	// 发送浏览器通知
	c.notificationService.SendBrowserNotification(c.sseHub, alert)

	// 清除相关缓存
	c.cache.Delete("alert_stats")

	logrus.Infof("告警已创建: Level=%s, Reason=%s, TrackID=%s",
		alert.Level, alert.Reason, alert.TrackID)

	ctx.JSON(http.StatusCreated, gin.H{
		"message": "告警创建成功",
		"alert":   alert,
	})
}

// GetRecentAlerts 获取最近告警
func (c *AlertController) GetRecentAlerts(ctx *gin.Context) {
	minutesStr := ctx.DefaultQuery("minutes", "60")
	cacheKey := "recent_alerts_" + minutesStr

	if alerts, found := c.cache.Get(cacheKey); found {
		ctx.JSON(http.StatusOK, alerts)
		return
	}

	minutes, err := strconv.Atoi(minutesStr)
	if err != nil || minutes <= 0 {
		ctx.JSON(http.StatusBadRequest, gin.H{"error": "无效的分钟参数"})
		return
	}

	since := time.Now().Add(-time.Duration(minutes) * time.Minute)
	alerts, err := c.alertRepo.FindRecentSince(since)
	if err != nil {
		logrus.Errorf("查询最近告警失败: %v", err)
		ctx.JSON(http.StatusInternalServerError, gin.H{"error": "查询告警失败"})
		return
	}

	c.cache.Set(cacheKey, alerts, 1*time.Minute)
	ctx.JSON(http.StatusOK, alerts)
}

// GetAlertsByLevel 根据级别获取告警
func (c *AlertController) GetAlertsByLevel(ctx *gin.Context) {
	level := ctx.Param("level")
	if level == "" {
		ctx.JSON(http.StatusBadRequest, gin.H{"error": "级别不能为空"})
		return
	}

	alerts, err := c.alertRepo.FindByLevel(level)
	if err != nil {
		logrus.Errorf("查询级别告警失败: %v", err)
		ctx.JSON(http.StatusInternalServerError, gin.H{"error": "查询告警失败"})
		return
	}

	ctx.JSON(http.StatusOK, alerts)
}

// GetAlertStats 获取告警统计
func (c *AlertController) GetAlertStats(ctx *gin.Context) {
	cacheKey := "alert_stats"

	if stats, found := c.cache.Get(cacheKey); found {
		ctx.JSON(http.StatusOK, stats)
		return
	}

	count, err := c.alertRepo.Count()
	if err != nil {
		logrus.Errorf("获取告警统计失败: %v", err)
		ctx.JSON(http.StatusInternalServerError, gin.H{"error": "获取统计失败"})
		return
	}

	stats := gin.H{
		"totalAlerts": count,
		"timestamp":   time.Now().Format(time.RFC3339),
	}

	c.cache.Set(cacheKey, stats, 2*time.Minute)
	ctx.JSON(http.StatusOK, stats)
}
