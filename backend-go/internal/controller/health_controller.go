package controller

import (
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
)

type HealthController struct{}

func NewHealthController() *HealthController {
	return &HealthController{}
}

// GetHealth 健康检查
func (c *HealthController) GetHealth(ctx *gin.Context) {
	ctx.JSON(http.StatusOK, gin.H{
		"status":    "ok",
		"service":   "baby-safety-monitor-backend",
		"version":   "1.0.0",
		"timestamp": time.Now().Format(time.RFC3339),
		"uptime":    time.Since(time.Now()).String(),
	})
}

// GetInfo 服务信息
func (c *HealthController) GetInfo(ctx *gin.Context) {
	ctx.JSON(http.StatusOK, gin.H{
		"name":        "婴儿安全监控系统后端",
		"version":     "1.0.0",
		"description": "基于Go语言重构的高性能后端服务",
		"features": []string{
			"实时SSE事件推送",
			"SQLite数据库存储",
			"钉钉通知集成",
			"RESTful API",
			"高并发处理",
		},
		"endpoints": map[string]string{
			"health":       "/health",
			"events":       "/api/events",
			"alerts":       "/api/alerts",
			"danger_zones": "/api/zones",
			"sse_stream":   "/api/events/stream",
		},
	})
}
