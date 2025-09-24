import { useEffect } from 'react'
import './App.css'
import { useStore } from './store'

function App() {
  const connect = useStore(s => s.connect)
  const events = useStore(s => s.events)
  const alerts = useStore(s => s.alerts)

  useEffect(() => { connect() }, [connect])

  return (
    <>
      <h1>Baby Safety Monitor</h1>
      <div className="card">
        <h2>实时事件</h2>
        <ul>
          {events.slice(0, 10).map((e, i) => (
            <li key={i}>{(e.timestamp ?? '').toString()} track:{e.trackId} bbox:[{e.x},{e.y},{e.w},{e.h}] action:{e.action ?? ''} risk:{e.riskScore ?? ''}</li>
          ))}
        </ul>
        <h2>告警</h2>
        <ul>
          {alerts.slice(0, 10).map((a, i) => (
            <li key={i}>{(a.timestamp ?? '').toString()} level:{a.level} reason:{a.reason ?? ''} track:{a.trackId ?? ''}</li>
          ))}
        </ul>
      </div>
    </>
  )
}

export default App
