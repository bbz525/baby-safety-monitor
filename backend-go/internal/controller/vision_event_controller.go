package controller

import (
	"baby-safety-monitor/internal/models"
	"baby-safety-monitor/internal/repository"
	"baby-safety-monitor/internal/service"
	"net/http"
	"strconv"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/sirupsen/logrus"
)

type VisionEventController struct {
	visionEventRepo *repository.VisionEventRepository
	sseHub          *service.SSEHub
}

func NewVisionEventController(sseHub *service.SSEHub) *VisionEventController {
	return &VisionEventController{
		visionEventRepo: repository.NewVisionEventRepository(),
		sseHub:          sseHub,
	}
}

// CreateVisionEvent 创建视觉事件
func (c *VisionEventController) CreateVisionEvent(ctx *gin.Context) {
	var req models.VisionEventRequest
	if err := ctx.ShouldBindJSON(&req); err != nil {
		ctx.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// 转换为VisionEvent
	event := req.ToVisionEvent()

	// 保存到数据库
	if err := c.visionEventRepo.Create(event); err != nil {
		logrus.Errorf("保存视觉事件失败: %v", err)
		ctx.JSON(http.StatusInternalServerError, gin.H{"error": "保存事件失败"})
		return
	}

	// 通过SSE发送事件
	c.sseHub.Send(map[string]interface{}{
		"type":      "vision_event",
		"timestamp": event.Timestamp.Format(time.RFC3339),
		"data":      event,
	})

	logrus.Infof("视觉事件已创建: TrackID=%s, Action=%s, RiskScore=%.2f", 
		event.TrackID, event.Action, event.RiskScore)

	ctx.JSON(http.StatusCreated, gin.H{
		"message": "事件创建成功",
		"event":   event,
	})
}

// GetRecentEvents 获取最近事件
func (c *VisionEventController) GetRecentEvents(ctx *gin.Context) {
	// 获取分钟参数
	minutesStr := ctx.DefaultQuery("minutes", "10")
	minutes, err := strconv.Atoi(minutesStr)
	if err != nil || minutes <= 0 {
		ctx.JSON(http.StatusBadRequest, gin.H{"error": "无效的分钟参数"})
		return
	}

	// 计算时间范围
	since := time.Now().Add(-time.Duration(minutes) * time.Minute)

	// 查询事件
	events, err := c.visionEventRepo.FindRecentSince(since)
	if err != nil {
		logrus.Errorf("查询最近事件失败: %v", err)
		ctx.JSON(http.StatusInternalServerError, gin.H{"error": "查询事件失败"})
		return
	}

	ctx.JSON(http.StatusOK, events)
}

// GetEventsByTrackID 根据TrackID获取事件
func (c *VisionEventController) GetEventsByTrackID(ctx *gin.Context) {
	trackID := ctx.Param("trackId")
	if trackID == "" {
		ctx.JSON(http.StatusBadRequest, gin.H{"error": "TrackID不能为空"})
		return
	}

	events, err := c.visionEventRepo.FindByTrackID(trackID)
	if err != nil {
		logrus.Errorf("查询TrackID事件失败: %v", err)
		ctx.JSON(http.StatusInternalServerError, gin.H{"error": "查询事件失败"})
		return
	}

	ctx.JSON(http.StatusOK, events)
}

// GetEventStats 获取事件统计
func (c *VisionEventController) GetEventStats(ctx *gin.Context) {
	count, err := c.visionEventRepo.Count()
	if err != nil {
		logrus.Errorf("获取事件统计失败: %v", err)
		ctx.JSON(http.StatusInternalServerError, gin.H{"error": "获取统计失败"})
		return
	}

	ctx.JSON(http.StatusOK, gin.H{
		"totalEvents": count,
		"timestamp":   time.Now().Format(time.RFC3339),
	})
}
