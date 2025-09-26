package main

import (
	"baby-safety-monitor/internal/controller"
	"baby-safety-monitor/internal/database"
	"baby-safety-monitor/internal/service"
	"log"
	"os"
	"os/signal"
	"syscall"

	"github.com/gin-gonic/gin"
	"github.com/sirupsen/logrus"
)

func main() {
	// 设置日志级别
	logrus.SetLevel(logrus.InfoLevel)
	logrus.SetFormatter(&logrus.TextFormatter{
		FullTimestamp: true,
	})

	// 初始化数据库
	if err := database.InitDatabase(); err != nil {
		log.Fatalf("数据库初始化失败: %v", err)
	}

	// 创建SSE Hub
	sseHub := service.NewSSEHub()
	go sseHub.Run()

	// 创建控制器
	visionEventController := controller.NewVisionEventController(sseHub)
	alertController := controller.NewAlertController(sseHub)
	dangerZoneController := controller.NewDangerZoneController()

	// 设置Gin模式
	if os.Getenv("GIN_MODE") == "" {
		gin.SetMode(gin.ReleaseMode)
	}

	// 创建路由
	router := gin.New()
	router.Use(gin.Logger())
	router.Use(gin.Recovery())

	// CORS中间件
	router.Use(func(c *gin.Context) {
		c.Header("Access-Control-Allow-Origin", "*")
		c.Header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		c.Header("Access-Control-Allow-Headers", "Content-Type, Authorization")

		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(204)
			return
		}

		c.Next()
	})

	// 健康检查
	router.GET("/health", func(c *gin.Context) {
		c.JSON(200, gin.H{
			"status":    "ok",
			"service":   "baby-safety-monitor-backend",
			"version":   "1.0.0",
			"timestamp": "2025-09-25T10:00:00Z",
		})
	})

	// API路由组
	api := router.Group("/api")
	{
		// 视觉事件路由
		events := api.Group("/events")
		{
			events.POST("/vision", visionEventController.CreateVisionEvent)
			events.GET("/recent", visionEventController.GetRecentEvents)
			events.GET("/track/:trackId", visionEventController.GetEventsByTrackID)
			events.GET("/stats", visionEventController.GetEventStats)
			events.GET("/stream", sseHub.HandleSSE)
		}

		// 告警路由
		alerts := api.Group("/alerts")
		{
			alerts.POST("/", alertController.CreateAlert)
			alerts.GET("/recent", alertController.GetRecentAlerts)
			alerts.GET("/level/:level", alertController.GetAlertsByLevel)
			alerts.GET("/stats", alertController.GetAlertStats)
		}

		// 危险区域路由
		zones := api.Group("/zones")
		{
			zones.POST("/", dangerZoneController.CreateDangerZone)
			zones.GET("/", dangerZoneController.GetDangerZones)
			zones.GET("/enabled", dangerZoneController.GetEnabledDangerZones)
			zones.GET("/:id", dangerZoneController.GetDangerZone)
			zones.PUT("/:id", dangerZoneController.UpdateDangerZone)
			zones.DELETE("/:id", dangerZoneController.DeleteDangerZone)
		}
	}

	// 启动服务器
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	logrus.Infof("服务器启动在端口 %s", port)

	// 设置优雅关闭
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		if err := router.Run(":" + port); err != nil {
			log.Fatalf("服务器启动失败: %v", err)
		}
	}()

	// 等待退出信号
	<-quit
	logrus.Println("正在关闭服务器...")

	// 关闭数据库连接
	if err := database.Close(); err != nil {
		logrus.Errorf("关闭数据库失败: %v", err)
	}

	logrus.Println("服务器已关闭")
}
