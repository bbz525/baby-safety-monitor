package database

import (
	"baby-safety-monitor/internal/models"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"time"

	"github.com/gin-gonic/gin"
	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
)

var DB *gorm.DB

// InitDatabase 初始化数据库
func InitDatabase() error {
	// 确保数据目录存在
	dataDir := "data"
	if err := os.MkdirAll(dataDir, 0755); err != nil {
		return err
	}

	// 数据库文件路径
	dbPath := filepath.Join(dataDir, "baby_safety.db")

	// 启用WAL模式以提高并发性能
	dsn := fmt.Sprintf("%s?_journal_mode=WAL", dbPath)

	// 根据环境设置日志级别
	logLevel := logger.Info
	if gin.Mode() == gin.ReleaseMode {
		logLevel = logger.Warn
	}

	// 连接数据库
	var err error
	DB, err = gorm.Open(sqlite.Open(dsn), &gorm.Config{
		Logger: logger.Default.LogMode(logLevel),
	})
	if err != nil {
		return err
	}

	// 配置连接池
	if sqlDB, err := DB.DB(); err == nil {
		sqlDB.SetMaxOpenConns(25)                 // 最大打开连接数
		sqlDB.SetMaxIdleConns(10)                 // 最大空闲连接数
		sqlDB.SetConnMaxLifetime(5 * time.Minute) // 连接最大生存时间
	} else {
		return fmt.Errorf("配置连接池失败: %v", err)
	}

	// 自动迁移
	if err := autoMigrate(); err != nil {
		return err
	}

	log.Println("数据库初始化成功")
	return nil
}

// autoMigrate 自动迁移数据库表
func autoMigrate() error {
	return DB.AutoMigrate(
		&models.VisionEvent{},
		&models.Alert{},
		&models.DangerZone{},
	)
}

// GetDB 获取数据库实例
func GetDB() *gorm.DB {
	return DB
}

// HealthCheck 数据库健康检查
func HealthCheck() error {
	if DB == nil {
		return fmt.Errorf("数据库未初始化")
	}

	sqlDB, err := DB.DB()
	if err != nil {
		return fmt.Errorf("获取SQL DB失败: %v", err)
	}

	return sqlDB.Ping()
}

// Close 关闭数据库连接
func Close() error {
	if DB != nil {
		sqlDB, err := DB.DB()
		if err != nil {
			return err
		}
		return sqlDB.Close()
	}
	return nil
}
