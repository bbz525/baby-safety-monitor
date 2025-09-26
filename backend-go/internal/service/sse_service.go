package service

import (
	"encoding/json"
	"fmt"
	"net/http"
	"sync"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/sirupsen/logrus"
)

// SSEHub SSE连接管理器
type SSEHub struct {
	clients    map[*SSEClient]bool
	register   chan *SSEClient
	unregister chan *SSEClient
	broadcast  chan interface{}
	mutex      sync.RWMutex
}

// SSEClient SSE客户端
type SSEClient struct {
	conn   gin.ResponseWriter
	events chan interface{}
	done   chan bool
}

// NewSSEHub 创建SSE Hub
func NewSSEHub() *SSEHub {
	return &SSEHub{
		clients:    make(map[*SSEClient]bool),
		register:   make(chan *SSEClient),
		unregister: make(chan *SSEClient),
		broadcast:  make(chan interface{}),
	}
}

// Run 运行SSE Hub
func (h *SSEHub) Run() {
	for {
		select {
		case client := <-h.register:
			h.mutex.Lock()
			h.clients[client] = true
			h.mutex.Unlock()
			logrus.Infof("SSE客户端已连接，当前连接数: %d", len(h.clients))

		case client := <-h.unregister:
			h.mutex.Lock()
			if _, ok := h.clients[client]; ok {
				delete(h.clients, client)
				close(client.events)
				close(client.done)
			}
			h.mutex.Unlock()
			logrus.Infof("SSE客户端已断开，当前连接数: %d", len(h.clients))

		case message := <-h.broadcast:
			h.mutex.RLock()
			for client := range h.clients {
				select {
				case client.events <- message:
				default:
					// 客户端缓冲区满，移除客户端
					delete(h.clients, client)
					close(client.events)
					close(client.done)
				}
			}
			h.mutex.RUnlock()
		}
	}
}

// Send 发送消息到所有客户端
func (h *SSEHub) Send(data interface{}) {
	select {
	case h.broadcast <- data:
	default:
		// 广播通道满，记录警告
		logrus.Warn("SSE广播通道已满，消息被丢弃")
	}
}

// HandleSSE 处理SSE连接
func (h *SSEHub) HandleSSE(c *gin.Context) {
	// 设置SSE响应头
	c.Header("Content-Type", "text/event-stream")
	c.Header("Cache-Control", "no-cache")
	c.Header("Connection", "keep-alive")
	c.Header("Access-Control-Allow-Origin", "*")
	c.Header("Access-Control-Allow-Headers", "Cache-Control")

	// 创建SSE客户端
	client := &SSEClient{
		conn:   c.Writer,
		events: make(chan interface{}, 256),
		done:   make(chan bool),
	}

	// 注册客户端
	h.register <- client

	// 发送初始连接消息
	initialMessage := map[string]interface{}{
		"type":      "connected",
		"timestamp": time.Now().Format(time.RFC3339),
		"message":   "SSE连接已建立",
	}
	h.sendSSEMessage(c.Writer, initialMessage)

	// 处理客户端消息
	go func() {
		defer func() {
			h.unregister <- client
		}()

		for {
			select {
			case event := <-client.events:
				if err := h.sendSSEMessage(c.Writer, event); err != nil {
					logrus.Errorf("发送SSE消息失败: %v", err)
					return
				}
			case <-client.done:
				return
			case <-c.Request.Context().Done():
				return
			}
		}
	}()

	// 保持连接
	<-c.Request.Context().Done()
}

// sendSSEMessage 发送SSE消息
func (h *SSEHub) sendSSEMessage(w gin.ResponseWriter, data interface{}) error {
	// 序列化数据
	jsonData, err := json.Marshal(data)
	if err != nil {
		return fmt.Errorf("序列化数据失败: %v", err)
	}

	// 发送SSE格式消息
	message := fmt.Sprintf("data: %s\n\n", string(jsonData))

	// 写入响应
	if _, err := w.Write([]byte(message)); err != nil {
		return fmt.Errorf("写入响应失败: %v", err)
	}

	// 刷新响应
	if flusher, ok := w.(http.Flusher); ok {
		flusher.Flush()
	}

	return nil
}

// GetClientCount 获取客户端数量
func (h *SSEHub) GetClientCount() int {
	h.mutex.RLock()
	defer h.mutex.RUnlock()
	return len(h.clients)
}
