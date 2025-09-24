import { useEffect } from 'react'
import './App.css'
import { useStore } from './store'

function App() {
  const connect = useStore(s => s.connect)
  const events = useStore(s => s.events)
  const alerts = useStore(s => s.alerts)
  const connected = useStore(s => s.connected)
  const lastError = useStore(s => s.lastError)

  useEffect(() => { connect() }, [connect])

  return (
    <>
      <h1>Baby Safety Monitor</h1>
      <div className="status">
        连接状态：{connected ? <span className='ok'>已连接</span> : <span className='bad'>未连接</span>} {lastError ? `(${lastError})` : ''}
      </div>
      <div className="grid">
        <div className="panel">
          <h2>
            实时事件 <span className='meta'>共 {events.length} 条</span>
            <span className='toolbar'>
              <button onClick={() => window.location.reload()}>刷新</button>
              <button onClick={() => { /* 清空事件 */ (useStore.setState as any)({ events: [] }); }}>清空</button>
            </span>
          </h2>
          <ul>
            {events.slice(0, 20).map((e, i) => (
              <li key={i}>
                <span className={
                  'risk ' + ((e.riskScore ?? 0) >= 0.9 ? 'high' : (e.riskScore ?? 0) >= 0.6 ? 'mid' : 'low')
                }>{(e.riskScore ?? 0).toFixed(2)}</span>
                <span className='meta'>{(e.timestamp ?? '').toString()}</span>
                <div>track:{e.trackId} bbox:[{e.x},{e.y},{e.w},{e.h}] action:{e.action ?? ''}</div>
              </li>
            ))}
          </ul>
        </div>
        <div className="panel">
          <h2>
            告警 <span className='meta'>共 {alerts.length} 条</span>
            <span className='toolbar'>
              <button onClick={() => window.location.reload()}>刷新</button>
              <button onClick={() => { /* 清空告警 */ (useStore.setState as any)({ alerts: [] }); }}>清空</button>
            </span>
          </h2>
          <ul>
            {alerts.slice(0, 20).map((a, i) => (
              <li key={i}>
                <span className={'risk ' + (a.level === 'critical' ? 'high' : a.level === 'warn' ? 'mid' : 'low')}>{a.level}</span>
                <span className='meta'>{(a.timestamp ?? '').toString()}</span>
                <div>reason:{a.reason ?? ''} track:{a.trackId ?? ''}</div>
                {/* 解析详情中的图片URL */}
                {(() => {
                  try {
                    const detail = a.detailsJson ? JSON.parse(a.detailsJson) : undefined;
                    const img = detail?.imageUrl as string | undefined;
                    if (!img) return null;
                    return <div style={{marginTop: 8}}>
                      <img src={img} alt="alert" style={{maxWidth: '100%', borderRadius: 6, border: '1px solid #eee'}} />
                    </div>;
                  } catch { return null; }
                })()}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </>
  )
}

export default App
