package middleware

import (
	"crypto/md5"
	"fmt"
	"sync"
	"time"

	"github.com/gin-gonic/gin"
)

// CacheItem 缓存项
type CacheItem struct {
	Data      []byte
	ExpiresAt time.Time
	Headers   map[string]string
}

// InMemoryCache 内存缓存
type InMemoryCache struct {
	mu    sync.RWMutex
	items map[string]*CacheItem
	ttl   time.Duration
	max   int
}

// NewInMemoryCache 创建新的内存缓存
func NewInMemoryCache(ttl time.Duration, maxEntries int) *InMemoryCache {
	cache := &InMemoryCache{
		items: make(map[string]*CacheItem),
		ttl:   ttl,
		max:   maxEntries,
	}
	
	// 定期清理过期项
	go cache.cleanup()
	
	return cache
}

// Get 获取缓存项
func (c *InMemoryCache) Get(key string) (*CacheItem, bool) {
	c.mu.RLock()
	defer c.mu.RUnlock()
	
	item, exists := c.items[key]
	if !exists || time.Now().After(item.ExpiresAt) {
		return nil, false
	}
	
	return item, true
}

// Set 设置缓存项
func (c *InMemoryCache) Set(key string, data []byte, headers map[string]string) {
	c.mu.Lock()
	defer c.mu.Unlock()
	
	// 如果超过最大条目数，删除最旧的
	if len(c.items) >= c.max {
		c.evictOldest()
	}
	
	c.items[key] = &CacheItem{
		Data:      data,
		ExpiresAt: time.Now().Add(c.ttl),
		Headers:   headers,
	}
}

// evictOldest 删除最旧的缓存项
func (c *InMemoryCache) evictOldest() {
	var oldestKey string
	var oldestTime time.Time
	
	for key, item := range c.items {
		if oldestKey == "" || item.ExpiresAt.Before(oldestTime) {
			oldestKey = key
			oldestTime = item.ExpiresAt
		}
	}
	
	if oldestKey != "" {
		delete(c.items, oldestKey)
	}
}

// cleanup 定期清理过期项
func (c *InMemoryCache) cleanup() {
	ticker := time.NewTicker(time.Minute)
	defer ticker.Stop()
	
	for range ticker.C {
		c.mu.Lock()
		now := time.Now()
		
		for key, item := range c.items {
			if now.After(item.ExpiresAt) {
				delete(c.items, key)
			}
		}
		c.mu.Unlock()
	}
}

// generateCacheKey 生成缓存键
func generateCacheKey(c *gin.Context) string {
	key := fmt.Sprintf("%s:%s", c.Request.Method, c.Request.URL.Path)
	if c.Request.URL.RawQuery != "" {
		key += "?" + c.Request.URL.RawQuery
	}
	
	return fmt.Sprintf("%x", md5.Sum([]byte(key)))
}

// CacheMiddleware 缓存中间件
func CacheMiddleware(cache *InMemoryCache) gin.HandlerFunc {
	return func(c *gin.Context) {
		// 只缓存GET请求
		if c.Request.Method != "GET" {
			c.Next()
			return
		}
		
		// 生成缓存键
		cacheKey := generateCacheKey(c)
		
		// 尝试从缓存获取
		if item, exists := cache.Get(cacheKey); exists {
			// 设置响应头
			for key, value := range item.Headers {
				c.Header(key, value)
			}
			
			c.Header("X-Cache", "HIT")
			c.Data(200, "application/json", item.Data)
			c.Abort()
			return
		}
		
		// 缓存未命中，继续处理请求
		c.Header("X-Cache", "MISS")
		
		// 使用ResponseWriter包装器来捕获响应
		writer := &responseWriter{
			ResponseWriter: c.Writer,
			cache:          cache,
			cacheKey:       cacheKey,
			headers:        make(map[string]string),
		}
		c.Writer = writer
		
		c.Next()
	}
}

// responseWriter 响应写入器包装器
type responseWriter struct {
	gin.ResponseWriter
	cache    *InMemoryCache
	cacheKey string
	headers  map[string]string
	data     []byte
}

// Write 写入响应数据
func (w *responseWriter) Write(data []byte) (int, error) {
	w.data = append(w.data, data...)
	return w.ResponseWriter.Write(data)
}

// WriteHeader 写入响应头
func (w *responseWriter) WriteHeader(code int) {
	// 只缓存成功响应
	if code == 200 {
		// 复制需要缓存的响应头
		for key, values := range w.ResponseWriter.Header() {
			if len(values) > 0 {
				w.headers[key] = values[0]
			}
		}
		
		// 在响应完成后缓存数据
		go func() {
			if len(w.data) > 0 {
				w.cache.Set(w.cacheKey, w.data, w.headers)
			}
		}()
	}
	
	w.ResponseWriter.WriteHeader(code)
}