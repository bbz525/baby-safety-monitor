import { useEffect, useState } from 'react'
import './App.css'
import { useStore, type VisionEvent, type Alert, type Camera } from './store'

type IconName = 'refresh' | 'clear' | 'settings' | 'camera' | 'alert' | 'play' | 'stop'

type IconProps = {
  name: IconName
  className?: string
  size?: number
}

type RiskBadgeProps = {
  score?: number
  level?: 'high' | 'mid' | 'low' | Alert['level'] | null
}

type StatusIndicatorProps = {
  status: 'running' | 'stopped' | 'error'
}

type TabButtonId = 'events' | 'alerts' | 'cameras'

type TabButtonProps = {
  id: TabButtonId
  label: string
  icon: IconName
  active: boolean
  onClick: (id: TabButtonId) => void
  count?: number | null
}

// 图标组件
const Icon = ({ name, className = "", size = 20 }: IconProps) => {
  const icons = {
    refresh: (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
        <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8" />
        <path d="M21 3v5h-5" />
        <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16" />
        <path d="M3 21v-5h5" />
      </svg>
    ),
    clear: (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
        <path d="M3 6h18" />
        <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
        <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
      </svg>
    ),
    settings: (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
        <circle cx="12" cy="12" r="3" />
        <path d="M12 1v6m0 6v6" />
        <path d="M21 12h-6m-6 0H3" />
      </svg>
    ),
    camera: (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
        <path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z" />
        <circle cx="12" cy="13" r="3" />
      </svg>
    ),
    alert: (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
        <line x1="12" y1="9" x2="12" y2="13" />
        <line x1="12" y1="17" x2="12.01" y2="17" />
      </svg>
    ),
    play: (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
        <polygon points="5,3 19,12 5,21" />
      </svg>
    ),
    stop: (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
        <rect x="6" y="6" width="12" height="12" />
      </svg>
    ),
  }
  
  return icons[name] || null
}

// 风险等级标识组件
const RiskBadge = ({ score = 0, level = null }: RiskBadgeProps) => {
  const riskLevel: 'high' | 'mid' | 'low' =
    level === 'critical'
      ? 'high'
      : level === 'warn'
      ? 'mid'
      : level === 'info'
      ? 'low'
      : level || (score >= 0.9 ? 'high' : score >= 0.6 ? 'mid' : 'low')

  const riskText =
    level === 'critical'
      ? '严重'
      : level === 'warn'
      ? '警告'
      : level === 'info'
      ? '信息'
      : level || (score >= 0.9 ? '高风险' : score >= 0.6 ? '中风险' : '低风险')
  
  return (
    <span className={`risk-badge risk-${riskLevel}`}>
      {level ? riskText : score?.toFixed(2)}
    </span>
  )
}

// 状态指示器组件
const StatusIndicator = ({ status }: StatusIndicatorProps) => {
  const statusConfig = {
    running: { text: '运行中', className: 'status-running' },
    stopped: { text: '已停止', className: 'status-stopped' },
    error: { text: '错误', className: 'status-error' }
  }
  
  const config = statusConfig[status] || statusConfig.stopped
  
  return (
    <span className={`status-indicator ${config.className}`}>
      <span className="status-dot"></span>
      {config.text}
    </span>
  )
}

// 标签页组件
const TabButton = ({ id, label, icon, active, onClick, count = null }: TabButtonProps) => (
  <button 
    className={`tab-button ${active ? 'active' : ''}`}
    onClick={() => onClick(id)}
  >
    <Icon name={icon} size={16} />
    <span>{label}</span>
    {count !== null && <span className="count-badge">{count}</span>}
  </button>
)

function App() {
  const connect = useStore(s => s.connect)
  const events = useStore(s => s.events)
  const alerts = useStore(s => s.alerts)
  const connected = useStore(s => s.connected)
  const lastError = useStore(s => s.lastError)
  const selectedTab = useStore(s => s.selectedTab || 'events')
  const setSelectedTab = useStore(s => s.setSelectedTab)
  
  const [cameras, setCameras] = useState<Camera[]>([])
  const [loading, setLoading] = useState<boolean>(false)

  useEffect(() => { 
    connect() 
    loadCameras()
  }, [connect])

  const loadCameras = async () => {
    try {
      setLoading(true)
      const response = await fetch('http://localhost:8001/cameras')
      if (response.ok) {
        const data: Camera[] = await response.json()
        setCameras(data)
      }
    } catch (error) {
      console.error('加载摄像头失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCameraAction = async (cameraId: Camera['id'], action: 'start' | 'stop') => {
    try {
      const response = await fetch(`http://localhost:8001/cameras/${cameraId}/${action}`, {
        method: 'POST'
      })
      if (response.ok) {
        loadCameras() // 重新加载摄像头状态
      }
    } catch (error) {
      console.error(`${action}摄像头失败:`, error)
    }
  }

  const formatTime = (timestamp: string | number | Date | null | undefined) => {
    if (!timestamp) return ''
    return new Date(timestamp).toLocaleTimeString('zh-CN')
  }

  const renderEvents = () => (
    <div className="panel">
      <div className="panel-header">
        <h2>
          实时事件 
          <span className="meta">共 {events.length} 条</span>
        </h2>
        <div className="toolbar">
          <button onClick={() => window.location.reload()}>
            <Icon name="refresh" size={16} />
            刷新
          </button>
          <button onClick={() => useStore.setState({ events: [] })}>
            <Icon name="clear" size={16} />
            清空
          </button>
        </div>
      </div>
      <div className="data-list">
        {events.slice(0, 50).map((e: VisionEvent, i: number) => (
          <div key={i} className="event-item">
            <div className="event-header">
              <RiskBadge score={e.riskScore} />
              <span className="meta">{formatTime(e.timestamp)}</span>
            </div>
            <div className="event-details">
              <div>轨迹: {e.trackId}</div>
              <div>位置: [{e.x}, {e.y}, {e.w}, {e.h}]</div>
              <div>动作: {e.action || '未知'}</div>
            </div>
          </div>
        ))}
        {events.length === 0 && (
          <div className="empty-state">暂无检测事件</div>
        )}
      </div>
    </div>
  )

  const renderAlerts = () => (
    <div className="panel">
      <div className="panel-header">
        <h2>
          告警记录 
          <span className="meta">共 {alerts.length} 条</span>
        </h2>
        <div className="toolbar">
          <button onClick={() => window.location.reload()}>
            <Icon name="refresh" size={16} />
            刷新
          </button>
          <button onClick={() => useStore.setState({ alerts: [] })}>
            <Icon name="clear" size={16} />
            清空
          </button>
        </div>
      </div>
      <div className="data-list">
        {alerts.slice(0, 50).map((a: Alert, i: number) => (
          <div key={i} className="alert-item">
            <div className="alert-header">
              <RiskBadge level={a.level} />
              <span className="meta">{formatTime(a.timestamp)}</span>
            </div>
            <div className="alert-details">
              <div>原因: {a.reason || '未知'}</div>
              <div>轨迹: {a.trackId || '无'}</div>
              {a.detailsJson && (() => {
                try {
                  const detail = JSON.parse(a.detailsJson)
                  return detail.imageUrl && (
                    <div className="alert-image">
                      <img src={detail.imageUrl} alt="告警截图" />
                    </div>
                  )
                } catch { return null }
              })()}
            </div>
          </div>
        ))}
        {alerts.length === 0 && (
          <div className="empty-state">暂无告警记录</div>
        )}
      </div>
    </div>
  )

  const renderCameras = () => (
    <div className="panel">
      <div className="panel-header">
        <h2>
          摄像头管理 
          <span className="meta">共 {cameras.length} 个</span>
        </h2>
        <div className="toolbar">
          <button onClick={loadCameras} disabled={loading}>
            <Icon name="refresh" size={16} />
            {loading ? '加载中...' : '刷新'}
          </button>
        </div>
      </div>
      <div className="camera-grid">
        {cameras.map((camera: Camera) => (
          <div key={camera.id} className="camera-card">
            <div className="camera-header">
              <Icon name="camera" size={20} />
              <h3>{camera.name}</h3>
              <StatusIndicator status={camera.status} />
            </div>
            <div className="camera-details">
              <div>类型: {camera.type}</div>
              <div>分辨率: {camera.resolution}px</div>
              <div>帧率: {camera.fps} FPS</div>
              {camera.lastError && (
                <div className="error-text">错误: {camera.lastError}</div>
              )}
            </div>
            <div className="camera-actions">
              {camera.status === 'running' ? (
                <button 
                  className="btn-stop"
                  onClick={() => handleCameraAction(camera.id, 'stop')}
                >
                  <Icon name="stop" size={16} />
                  停止
                </button>
              ) : (
                <button 
                  className="btn-start"
                  onClick={() => handleCameraAction(camera.id, 'start')}
                >
                  <Icon name="play" size={16} />
                  启动
                </button>
              )}
            </div>
          </div>
        ))}
        {cameras.length === 0 && (
          <div className="empty-state">暂无摄像头配置</div>
        )}
      </div>
    </div>
  )

  return (
    <div className="app">
      <header className="app-header">
        <h1>
          <Icon name="camera" size={24} />
          婴儿安全监控系统
        </h1>
        
        <div className="connection-status">
          <span className={`status-indicator ${connected ? 'status-running' : 'status-error'}`}>
            <span className="status-dot"></span>
            {connected ? '已连接' : '未连接'}
          </span>
          {lastError && <span className="error-text">({lastError})</span>}
        </div>
      </header>

      <nav className="app-nav">
        <TabButton
          id="events"
          label="实时事件"
          icon="refresh"
          active={selectedTab === 'events'}
          onClick={setSelectedTab}
          count={events.length}
        />
        <TabButton
          id="alerts"
          label="告警记录"
          icon="alert"
          active={selectedTab === 'alerts'}
          onClick={setSelectedTab}
          count={alerts.length}
        />
        <TabButton
          id="cameras"
          label="摄像头"
          icon="camera"
          active={selectedTab === 'cameras'}
          onClick={setSelectedTab}
          count={cameras.filter(c => c.status === 'running').length}
        />
      </nav>

      <main className="app-main">
        {selectedTab === 'events' && renderEvents()}
        {selectedTab === 'alerts' && renderAlerts()}
        {selectedTab === 'cameras' && renderCameras()}
      </main>
    </div>
  )
}

export default App