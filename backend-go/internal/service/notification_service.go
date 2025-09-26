package service

import (
	"bytes"
	"crypto/hmac"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"strconv"
	"time"

	"baby-safety-monitor/internal/models"

	"github.com/sirupsen/logrus"
)

// NotificationService 通知服务
type NotificationService struct {
	dingtalkWebhook string
	dingtalkSecret  string
	httpClient      *http.Client
}

// NewNotificationService 创建通知服务
func NewNotificationService() *NotificationService {
	return &NotificationService{
		dingtalkWebhook: os.Getenv("DINGTALK_WEBHOOK"),
		dingtalkSecret:  os.Getenv("DINGTALK_SECRET"),
		httpClient: &http.Client{
			Timeout: 10 * time.Second,
		},
	}
}

// SendDingtalkNotification 发送钉钉通知
func (s *NotificationService) SendDingtalkNotification(alert *models.Alert) error {
	if s.dingtalkWebhook == "" {
		logrus.Warn("钉钉Webhook未配置，跳过通知")
		return nil
	}

	// 构建消息内容
	message := s.buildDingtalkMessage(alert)

	// 发送请求
	req, err := http.NewRequest("POST", s.dingtalkWebhook, bytes.NewBuffer(message))
	if err != nil {
		return fmt.Errorf("创建请求失败: %v", err)
	}

	req.Header.Set("Content-Type", "application/json")

	// 如果有密钥，添加签名
	if s.dingtalkSecret != "" {
		timestamp := strconv.FormatInt(time.Now().UnixNano()/1e6, 10)
		sign := s.generateSign(timestamp, s.dingtalkSecret)

		req.URL.RawQuery = fmt.Sprintf("access_token=%s&timestamp=%s&sign=%s",
			s.dingtalkWebhook, timestamp, sign)
	}

	resp, err := s.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("发送请求失败: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("钉钉通知发送失败，状态码: %d", resp.StatusCode)
	}

	logrus.Infof("钉钉通知发送成功: %s", alert.Reason)
	return nil
}

// buildDingtalkMessage 构建钉钉消息
func (s *NotificationService) buildDingtalkMessage(alert *models.Alert) []byte {
	// 解析详情JSON
	var details map[string]interface{}
	if alert.DetailsJSON != "" {
		json.Unmarshal([]byte(alert.DetailsJSON), &details)
	}

	// 构建消息内容
	content := fmt.Sprintf(`
## 🚨 婴儿安全告警

**告警级别**: %s
**告警原因**: %s
**时间**: %s
**轨迹ID**: %s

### 详细信息
%s

---
*来自婴儿安全监控系统*
`, alert.Level, alert.Reason, alert.Timestamp.Format("2006-01-02 15:04:05"),
		alert.TrackID, s.formatDetails(details))

	message := map[string]interface{}{
		"msgtype": "markdown",
		"markdown": map[string]string{
			"title": "婴儿安全告警",
			"text":  content,
		},
	}

	jsonData, _ := json.Marshal(message)
	return jsonData
}

// formatDetails 格式化详情信息
func (s *NotificationService) formatDetails(details map[string]interface{}) string {
	if details == nil {
		return "无详细信息"
	}

	var result string
	for key, value := range details {
		result += fmt.Sprintf("- **%s**: %v\n", key, value)
	}
	return result
}

// generateSign 生成钉钉签名
func (s *NotificationService) generateSign(timestamp, secret string) string {
	stringToSign := timestamp + "\n" + secret
	h := hmac.New(sha256.New, []byte(secret))
	h.Write([]byte(stringToSign))
	return base64.StdEncoding.EncodeToString(h.Sum(nil))
}

// SendBrowserNotification 发送浏览器通知（通过SSE）
func (s *NotificationService) SendBrowserNotification(hub *SSEHub, alert *models.Alert) {
	notification := map[string]interface{}{
		"type":      "alert",
		"timestamp": alert.Timestamp.Format(time.RFC3339),
		"data":      alert,
	}

	hub.Send(notification)
	logrus.Infof("浏览器通知已发送: %s", alert.Reason)
}
