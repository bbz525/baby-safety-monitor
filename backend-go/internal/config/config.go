package config

import (
	"fmt"
	"os"
	"strconv"
	"time"
)

// Config 应用配置结构
type Config struct {
	Server   ServerConfig   `yaml:"server"`
	Database DatabaseConfig `yaml:"database"`
	Logging  LoggingConfig  `yaml:"logging"`
	SSE      SSEConfig      `yaml:"sse"`
	Cache    CacheConfig    `yaml:"cache"`
}

// ServerConfig 服务器配置
type ServerConfig struct {
	Port         string        `yaml:"port"`
	Mode         string        `yaml:"mode"`
	ReadTimeout  time.Duration `yaml:"read_timeout"`
	WriteTimeout time.Duration `yaml:"write_timeout"`
	IdleTimeout  time.Duration `yaml:"idle_timeout"`
}

// DatabaseConfig 数据库配置
type DatabaseConfig struct {
	Driver          string        `yaml:"driver"`
	DSN             string        `yaml:"dsn"`
	MaxOpenConns    int           `yaml:"max_open_conns"`
	MaxIdleConns    int           `yaml:"max_idle_conns"`
	ConnMaxLifetime time.Duration `yaml:"conn_max_lifetime"`
}

// LoggingConfig 日志配置
type LoggingConfig struct {
	Level  string `yaml:"level"`
	Format string `yaml:"format"`
}

// SSEConfig SSE配置
type SSEConfig struct {
	BufferSize   int           `yaml:"buffer_size"`
	PingInterval time.Duration `yaml:"ping_interval"`
	MaxClients   int           `yaml:"max_clients"`
}

// CacheConfig 缓存配置
type CacheConfig struct {
	Enabled    bool          `yaml:"enabled"`
	TTL        time.Duration `yaml:"ttl"`
	MaxEntries int           `yaml:"max_entries"`
}

// LoadConfig 加载配置
func LoadConfig() *Config {
	return &Config{
		Server: ServerConfig{
			Port:         getEnv("PORT", "8080"),
			Mode:         getEnv("GIN_MODE", "release"),
			ReadTimeout:  getDurationEnv("READ_TIMEOUT", 30*time.Second),
			WriteTimeout: getDurationEnv("WRITE_TIMEOUT", 30*time.Second),
			IdleTimeout:  getDurationEnv("IDLE_TIMEOUT", 60*time.Second),
		},
		Database: DatabaseConfig{
			Driver:          getEnv("DB_DRIVER", "sqlite"),
			DSN:             getEnv("DB_DSN", "data/baby_safety.db"),
			MaxOpenConns:    getIntEnv("DB_MAX_OPEN_CONNS", 25),
			MaxIdleConns:    getIntEnv("DB_MAX_IDLE_CONNS", 10),
			ConnMaxLifetime: getDurationEnv("DB_CONN_MAX_LIFETIME", 5*time.Minute),
		},
		Logging: LoggingConfig{
			Level:  getEnv("LOG_LEVEL", "info"),
			Format: getEnv("LOG_FORMAT", "text"),
		},
		SSE: SSEConfig{
			BufferSize:   getIntEnv("SSE_BUFFER_SIZE", 256),
			PingInterval: getDurationEnv("SSE_PING_INTERVAL", 30*time.Second),
			MaxClients:   getIntEnv("SSE_MAX_CLIENTS", 1000),
		},
		Cache: CacheConfig{
			Enabled:    getBoolEnv("CACHE_ENABLED", true),
			TTL:        getDurationEnv("CACHE_TTL", 5*time.Minute),
			MaxEntries: getIntEnv("CACHE_MAX_ENTRIES", 1000),
		},
	}
}

// 辅助函数
func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func getIntEnv(key string, defaultValue int) int {
	if str := os.Getenv(key); str != "" {
		if value, err := strconv.Atoi(str); err == nil {
			return value
		}
	}
	return defaultValue
}

func getBoolEnv(key string, defaultValue bool) bool {
	if str := os.Getenv(key); str != "" {
		if value, err := strconv.ParseBool(str); err == nil {
			return value
		}
	}
	return defaultValue
}

func getDurationEnv(key string, defaultValue time.Duration) time.Duration {
	if str := os.Getenv(key); str != "" {
		if value, err := time.ParseDuration(str); err == nil {
			return value
		}
	}
	return defaultValue
}

// Validate 验证配置
func (c *Config) Validate() error {
	if c.Server.Port == "" {
		return fmt.Errorf("server port cannot be empty")
	}
	if c.Database.DSN == "" {
		return fmt.Errorf("database DSN cannot be empty")
	}
	return nil
}