import { FormEvent, useEffect, useMemo, useState } from 'react'
import type { ConnectorState, ConnectorStatus, SidecarEvent } from './connectorBridge'

const INITIAL_STATE: ConnectorState = {
  status: 'offline',
  logs: [],
  isPaired: false,
  errorMessage: '',
}

const STATUS_LABELS: Record<ConnectorStatus, string> = {
  offline: 'Offline',
  pairing: 'Pairing',
  connecting: 'Connecting',
  online: 'Online',
  stopping: 'Stopping',
  error: 'Error',
}

export function App() {
  const [pairingCode, setPairingCode] = useState('')
  const [state, setState] = useState<ConnectorState>(INITIAL_STATE)
  const [isBusy, setIsBusy] = useState(false)

  useEffect(() => {
    void window.connector.getState().then(setState)
    const removeStateListener = window.connector.onState(setState)
    const removeUpdaterListener = window.connector.onUpdaterEvent((message) => {
      const updaterEvent: SidecarEvent = { type: 'updater', level: 'info', message, payload: {} }
      setState((current) => ({
        ...current,
        logs: [...current.logs, updaterEvent].slice(-200),
      }))
    })

    return () => {
      removeStateListener()
      removeUpdaterListener()
    }
  }, [])

  const latestLogs = useMemo(() => state.logs.slice(-8).reverse(), [state.logs])
  const canPair = pairingCode.trim().length > 0 && !isBusy && state.status !== 'online'
  const canStart = !isBusy && (state.status === 'offline' || state.status === 'error')
  const canStop = !isBusy && (state.status === 'online' || state.status === 'connecting')

  async function handlePair(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault()
    if (!canPair) {
      return
    }
    await runAction(() => window.connector.pairConnector(pairingCode))
  }

  async function handleStart(): Promise<void> {
    if (!canStart) {
      return
    }
    await runAction(() => window.connector.startConnector())
  }

  async function handleStop(): Promise<void> {
    if (!canStop) {
      return
    }
    await runAction(() => window.connector.stopConnector())
  }

  async function handleUpdateCheck(): Promise<void> {
    setIsBusy(true)
    try {
      await window.connector.checkForUpdates()
    } finally {
      setIsBusy(false)
    }
  }

  async function runAction(action: () => Promise<ConnectorState>): Promise<void> {
    setIsBusy(true)
    try {
      setState(await action())
    } finally {
      setIsBusy(false)
    }
  }

  return (
    <main className="app-shell">
      <section className="hero-panel glass-panel">
        <div className="hero-copy">
          <p className="eyebrow">Booking Home automation bridge</p>
          <h1>Facebook Group Connector</h1>
          <p className="hero-text">
            Kết nối dashboard cloud với browser local của khách hàng. Session Facebook luôn ở
            trên máy khách, connector chỉ nhận job đã được allowlist.
          </p>
        </div>
        <StatusBadge status={state.status} />
      </section>

      <section className="content-grid">
        <form className="glass-panel pairing-card" onSubmit={(event) => void handlePair(event)}>
          <div>
            <p className="section-kicker">Pairing code</p>
            <h2>Kết nối với dashboard</h2>
            <p className="muted">
              Tạo mã tại dashboard rồi nhập vào đây. Server mặc định:
              <span className="mono server-url"> https://schedule.bookinghome.one</span>
            </p>
          </div>

          <label className="field-label" htmlFor="pairing-code">
            Mã kết nối
          </label>
          <input
            id="pairing-code"
            className="pairing-input"
            value={pairingCode}
            placeholder="ABC123"
            autoComplete="one-time-code"
            onChange={(event) => setPairingCode(event.target.value.toUpperCase())}
          />

          <button className="primary-button" disabled={!canPair} type="submit">
            Pair connector
          </button>

          {state.errorMessage ? <p className="error-message">{state.errorMessage}</p> : null}
        </form>

        <section className="glass-panel control-card">
          <div>
            <p className="section-kicker">Connector runtime</p>
            <h2>Chạy nền an toàn</h2>
            <p className="muted">
              Đóng cửa sổ sẽ ẩn app xuống tray. Chọn Quit từ tray để dừng connector hoàn toàn.
            </p>
          </div>

          <div className="control-actions">
            <button className="primary-button" disabled={!canStart} onClick={() => void handleStart()}>
              Start Connector
            </button>
            <button className="secondary-button" disabled={!canStop} onClick={() => void handleStop()}>
              Stop
            </button>
          </div>

          <button className="text-button" disabled={isBusy} onClick={() => void handleUpdateCheck()}>
            Check for updates
          </button>
        </section>
      </section>

      <section className="glass-panel log-panel">
        <div className="log-header">
          <div>
            <p className="section-kicker">Activity log</p>
            <h2>Trạng thái gần đây</h2>
          </div>
          <span className="log-count">{state.logs.length} events</span>
        </div>
        <div className="log-list" aria-live="polite">
          {latestLogs.length > 0 ? (
            latestLogs.map((event, index) => <LogLine event={event} key={`${event.type}-${index}`} />)
          ) : (
            <p className="empty-log">Chưa có log. Pair connector để bắt đầu.</p>
          )}
        </div>
      </section>
    </main>
  )
}

function StatusBadge({ status }: { status: ConnectorStatus }) {
  return (
    <div className={`status-badge status-${status}`}>
      <span className="status-dot" />
      {STATUS_LABELS[status]}
    </div>
  )
}

function LogLine({ event }: { event: SidecarEvent }) {
  return (
    <article className={`log-line log-${event.level}`}>
      <span className="mono log-type">{event.type}</span>
      <span>{event.message}</span>
    </article>
  )
}
