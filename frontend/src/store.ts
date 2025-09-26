import { create } from 'zustand'
import { subscriptionsLogic } from 'zustand/middleware/subscriptions'

export interface VisionEvent {
  id?: string
  timestamp?: string
  trackId: string
  x: number
  y: number
  w: number
  h: number
  action?: string
  riskScore?: number
  cameraId?: string
}

export interface Alert {
  id?: string
  timestamp?: string
  trackId?: string
  zoneId?: number
  level: 'info' | 'warn' | 'critical'
  reason?: string
  detailsJson?: string
}

export interface Camera {
  id: string
  name: string
  source: string
  type: 'rtsp' | 'http' | 'file' | 'mac_camera'
  enabled: boolean
  fps: number
  resolution: number
  status: 'stopped' | 'running' | 'error'
  lastError?: string
  createdAt?: string
  updatedAt?: string
}

export interface AppState {
  // 连接状态
  connected: boolean
  lastError: string | null
  eventSource: EventSource | null
  
  // 数据
  events: VisionEvent[]
  alerts: Alert[]
  cameras: Camera[]
  
  // 统计信息
  stats: {
    totalEvents: number
    totalAlerts: number
    activeCameras: number
    avgRiskScore: number
  }
  
  // UI状态
  selectedTab: 'events' | 'alerts' | 'cameras' | 'analytics'
  showSettings: boolean
  darkMode: boolean
  autoRefresh: boolean
  refreshInterval: number
  
  // 过滤器
  filters: {
    riskLevel: 'all' | 'low' | 'medium' | 'high'
    timeRange: '1h' | '6h' | '24h' | 'all'
    cameraId: string | null
  }
  
  // 操作方法
  connect: () => void
  disconnect: () => void
  addEvent: (event: VisionEvent) => void
  addAlert: (alert: Alert) => void
  setCameras: (cameras: Camera[]) => void
  updateCamera: (id: string, updates: Partial<Camera>) => void
  setSelectedTab: (tab: 'events' | 'alerts' | 'cameras' | 'analytics') => void
  setShowSettings: (show: boolean) => void
  toggleDarkMode: () => void
  setAutoRefresh: (enabled: boolean) => void
  setFilters: (filters: Partial<typeof state.filters>) => void
  clearEvents: () => void
  clearAlerts: () => void
  refreshData: () => void
}

const initialState = {
  connected: false,
  lastError: null,
  eventSource: null,
  events: [],
  alerts: [],
  cameras: [],
  stats: {
    totalEvents: 0,
    totalAlerts: 0,
    activeCameras: 0,
    avgRiskScore: 0,
  },
  selectedTab: 'events' as const,
  showSettings: false,
  darkMode: localStorage.getItem('darkMode') === 'true',
  autoRefresh: true,
  refreshInterval: 5000,
  filters: {
    riskLevel: 'all' as const,
    timeRange: '1h' as const,
    cameraId: null,
  },
}

export const useStore = create<AppState>()((set, get) => ({
  ...initialState,
  
  connect: () => {
    const state = get()
    if (state.eventSource) {
      state.eventSource.close()
    }
    
    const baseUrl = import.meta.env.VITE_API_BASE || 'http://localhost:8080'
    const eventSource = new EventSource(`${baseUrl}/api/events/stream`)
    
    eventSource.onopen = () => {
      set({ connected: true, lastError: null, eventSource })
    }
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        
        // 检测事件类型
        if ('x' in data && 'y' in data && 'w' in data && 'h' in data) {
          // Vision事件
          get().addEvent(data)
        } else if ('level' in data) {
          // 告警事件
          get().addAlert(data)
        }
      } catch (error) {
        console.error('解析事件数据失败:', error)
      }
    }
    
    eventSource.onerror = () => {
      set({ 
        connected: false, 
        lastError: '连接中断，尝试重连...',
        eventSource: null 
      })
      
      // 自动重连
      setTimeout(() => {
        get().connect()
      }, 3000)
    }
  },
  
  disconnect: () => {
    const state = get()
    if (state.eventSource) {
      state.eventSource.close()
    }
    set({ connected: false, eventSource: null })
  },
  
  addEvent: (event) => {
    set((state) => {
      const newEvents = [event, ...state.events].slice(0, 1000) // 保持最新1000条
      const stats = {
        ...state.stats,
        totalEvents: state.stats.totalEvents + 1,
        avgRiskScore: newEvents.reduce((sum, e) => sum + (e.riskScore || 0), 0) / newEvents.length
      }
      return { events: newEvents, stats }
    })
  },
  
  addAlert: (alert) => {
    set((state) => {
      const newAlerts = [alert, ...state.alerts].slice(0, 500) // 保持最新500条
      const stats = {
        ...state.stats,
        totalAlerts: state.stats.totalAlerts + 1
      }
      return { alerts: newAlerts, stats }
    })
  },
  
  setCameras: (cameras) => {
    set((state) => {
      const activeCameras = cameras.filter(c => c.status === 'running').length
      const stats = { ...state.stats, activeCameras }
      return { cameras, stats }
    })
  },
  
  updateCamera: (id, updates) => {
    set((state) => ({
      cameras: state.cameras.map(camera => 
        camera.id === id ? { ...camera, ...updates } : camera
      )
    }))
  },
  
  setSelectedTab: (tab) => set({ selectedTab: tab }),
  setShowSettings: (show) => set({ showSettings: show }),
  
  toggleDarkMode: () => {
    set((state) => {
      const darkMode = !state.darkMode
      localStorage.setItem('darkMode', String(darkMode))
      document.documentElement.classList.toggle('dark', darkMode)
      return { darkMode }
    })
  },
  
  setAutoRefresh: (enabled) => set({ autoRefresh: enabled }),
  setFilters: (filters) => set((state) => ({ 
    filters: { ...state.filters, ...filters } 
  })),
  
  clearEvents: () => set({ events: [] }),
  clearAlerts: () => set({ alerts: [] }),
  
  refreshData: async () => {
    try {
      const baseUrl = import.meta.env.VITE_API_BASE || 'http://localhost:8080'
      const visionUrl = import.meta.env.VITE_VISION_BASE || 'http://localhost:8001'
      
      // 获取摄像头列表
      const cameraResponse = await fetch(`${visionUrl}/cameras`)
      if (cameraResponse.ok) {
        const cameras = await cameraResponse.json()
        get().setCameras(cameras)
      }
      
      // 获取最近事件
      const eventsResponse = await fetch(`${baseUrl}/api/events/recent?minutes=60`)
      if (eventsResponse.ok) {
        const recentEvents = await eventsResponse.json()
        set({ events: recentEvents })
      }
      
      // 获取最近告警
      const alertsResponse = await fetch(`${baseUrl}/api/alerts/recent?minutes=60`)
      if (alertsResponse.ok) {
        const recentAlerts = await alertsResponse.json()
        set({ alerts: recentAlerts })
      }
      
    } catch (error) {
      console.error('刷新数据失败:', error)
      set({ lastError: '刷新数据失败' })
    }
  },
}))

// 初始化
if (useStore.getState().darkMode) {
  document.documentElement.classList.add('dark')
}