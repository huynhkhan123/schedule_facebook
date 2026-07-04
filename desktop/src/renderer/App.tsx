import { FormEvent, useEffect, useMemo, useState } from 'react'
import type { ConnectorState, ConnectorStatus, SidecarEvent, UpdaterEvent, UpdaterStatus } from './connectorBridge'

const INITIAL_STATE: ConnectorState = {
  status: 'offline',
  logs: [],
  isPaired: false,
  errorMessage: '',
}

const INITIAL_UPDATER_EVENT: UpdaterEvent = {
  status: 'idle',
  message: 'Sẵn sàng kiểm tra bản mới.',
}

const STATUS_LABELS: Record<ConnectorStatus, string> = {
  offline: 'Chưa chạy',
  pairing: 'Đang kết nối',
  connecting: 'Đang chạy',
  online: 'Đã sẵn sàng',
  stopping: 'Đang dừng',
  error: 'Cần kiểm tra',
}

const STATUS_HINTS: Record<ConnectorStatus, string> = {
  offline: 'Connector đang nghỉ',
  pairing: 'Đang xác thực mã',
  connecting: 'Đang mở kênh cloud',
  online: 'Cloud bridge hoạt động',
  stopping: 'Đang đóng phiên chạy',
  error: 'Xem timeline để xử lý',
}

const UPDATER_LABELS: Record<UpdaterStatus, string> = {
  idle: 'Sẵn sàng',
  checking: 'Đang kiểm tra',
  available: 'Có bản mới',
  not_available: 'Mới nhất',
  downloading: 'Đang tải',
  downloaded: 'Chờ cài đặt',
  error: 'Lỗi cập nhật',
}

export function App() {
  const [pairingCode, setPairingCode] = useState('')
  const [state, setState] = useState<ConnectorState>(INITIAL_STATE)
  const [appVersion, setAppVersion] = useState('0.0.0')
  const [updaterEvent, setUpdaterEvent] = useState<UpdaterEvent>(INITIAL_UPDATER_EVENT)
  const [isBusy, setIsBusy] = useState(false)
  const [isBooting, setIsBooting] = useState(true)

  useEffect(() => {
    let isMounted = true
    let bootTimer: ReturnType<typeof setTimeout> | undefined
    const bootStartedAt = Date.now()

    async function hydrateApp(): Promise<void> {
      const [versionResult, stateResult] = await Promise.allSettled([
        window.connector.getAppVersion(),
        window.connector.getState(),
      ])

      if (!isMounted) {
        return
      }

      if (versionResult.status === 'fulfilled') {
        setAppVersion(versionResult.value)
      }

      if (stateResult.status === 'fulfilled') {
        setState(stateResult.value)
      } else {
        setState({
          ...INITIAL_STATE,
          status: 'error',
          errorMessage: getErrorMessage(stateResult.reason),
        })
      }

      const elapsed = Date.now() - bootStartedAt
      bootTimer = setTimeout(() => {
        if (isMounted) {
          setIsBooting(false)
        }
      }, Math.max(0, 900 - elapsed))
    }

    void hydrateApp()

    const removeStateListener = window.connector.onState(setState)
    const removeUpdaterListener = window.connector.onUpdaterEvent((event) => {
      setUpdaterEvent(event)
      const logEvent: SidecarEvent = {
        type: 'updater',
        level: event.status === 'error' ? 'error' : 'info',
        message: event.message,
        payload: { status: event.status, version: event.version ?? '', percent: event.percent ?? 0 },
      }
      setState((current) => ({
        ...current,
        logs: [...current.logs, logEvent].slice(-200),
      }))
    })

    return () => {
      isMounted = false
      if (bootTimer) {
        clearTimeout(bootTimer)
      }
      removeStateListener()
      removeUpdaterListener()
    }
  }, [])

  const latestLogs = useMemo(() => state.logs.slice(-6).reverse(), [state.logs])
  const canPair = pairingCode.trim().length > 0 && !isBusy && state.status !== 'online'
  const canStart = !isBusy && (state.status === 'offline' || state.status === 'error')
  const canStop = !isBusy && (state.status === 'online' || state.status === 'connecting')
  const profileLabel = state.isPaired ? 'Đã ghép' : 'Chưa ghép'
  const updateLabel = UPDATER_LABELS[updaterEvent.status] ?? updaterEvent.status

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
    } catch (error: unknown) {
      setUpdaterEvent({ status: 'error', message: getErrorMessage(error) })
    } finally {
      setIsBusy(false)
    }
  }

  async function runAction(action: () => Promise<ConnectorState>): Promise<void> {
    setIsBusy(true)
    try {
      setState(await action())
    } catch (error: unknown) {
      setState((current) => ({
        ...current,
        status: 'error',
        errorMessage: getErrorMessage(error),
      }))
    } finally {
      setIsBusy(false)
    }
  }

  if (isBooting) {
    return <LoadingScreen />
  }

  return (
    <main className="app-shell">
      <DashboardHeader appVersion={appVersion} status={state.status} />

      <section className="dashboard-grid" aria-label="Connector dashboard">
        <ConnectionHero
          status={state.status}
          isBusy={isBusy}
          canStart={canStart}
          canStop={canStop}
          onStart={() => void handleStart()}
          onStop={() => void handleStop()}
          onUpdateCheck={() => void handleUpdateCheck()}
        />

        <section className="metric-grid" aria-label="Tổng quan nhanh">
          <MetricCard label="Kết nối" value={STATUS_LABELS[state.status]} detail={STATUS_HINTS[state.status]} tone={state.status} />
          <MetricCard label="Profile" value={profileLabel} detail="Browser local" tone={state.isPaired ? 'online' : 'offline'} />
          <MetricCard label="Update" value={updateLabel} detail={updaterEvent.version ? `v${updaterEvent.version}` : 'Release channel'} tone={updaterEvent.status === 'error' ? 'error' : 'online'} />
          <MetricCard label="Events" value={String(state.logs.length)} detail="Timeline" tone="neutral" />
        </section>

        <section className="panel-grid">
          <PairingPanel
            pairingCode={pairingCode}
            errorMessage={state.errorMessage}
            canPair={canPair}
            isPaired={state.isPaired}
            onChangePairingCode={setPairingCode}
            onSubmit={(event) => void handlePair(event)}
          />
          <RuntimePanel
            status={state.status}
            updaterEvent={updaterEvent}
            appVersion={appVersion}
            isBusy={isBusy}
            canStart={canStart}
            canStop={canStop}
            onStart={() => void handleStart()}
            onStop={() => void handleStop()}
            onUpdateCheck={() => void handleUpdateCheck()}
          />
        </section>

        <ActivityTimeline events={latestLogs} totalEvents={state.logs.length} />
      </section>
    </main>
  )
}

function LoadingScreen() {
  return (
    <main className="loading-screen" aria-label="Đang khởi động Facebook Connector">
      <div className="loading-orb" aria-hidden="true">
        <span />
      </div>
      <div className="loading-copy">
        <p className="kicker">Booking Home</p>
        <h1>Facebook Connector</h1>
        <p>Đang khởi động workspace local</p>
      </div>
      <div className="boot-steps" aria-label="Tiến trình khởi động">
        <BootStep label="App shell" />
        <BootStep label="Connector state" />
        <BootStep label="Update channel" />
      </div>
    </main>
  )
}

function BootStep({ label }: { label: string }) {
  return (
    <span className="boot-step">
      <span className="boot-dot" />
      {label}
    </span>
  )
}

function DashboardHeader({ appVersion, status }: { appVersion: string; status: ConnectorStatus }) {
  return (
    <header className="dashboard-header">
      <div className="brand-lockup">
        <div className="brand-mark" aria-hidden="true">BH</div>
        <div>
          <p className="kicker">Desktop bridge</p>
          <h1>Facebook Connector</h1>
        </div>
      </div>
      <div className="header-meta">
        <span className="version-chip">v{appVersion}</span>
        <StatusPill status={status} />
      </div>
    </header>
  )
}

function ConnectionHero({
  status,
  isBusy,
  canStart,
  canStop,
  onStart,
  onStop,
  onUpdateCheck,
}: {
  status: ConnectorStatus
  isBusy: boolean
  canStart: boolean
  canStop: boolean
  onStart: () => void
  onStop: () => void
  onUpdateCheck: () => void
}) {
  return (
    <section className="hero-card surface-card">
      <div className="hero-ambient" aria-hidden="true" />
      <div className="hero-content">
        <p className="kicker">Cloud ↔ Local</p>
        <h2>{status === 'online' ? 'Workspace đã sẵn sàng' : 'Điều khiển browser local'}</h2>
        <p>Ghép máy, chạy connector, rồi thao tác Facebook trong profile bảo mật của khách.</p>
      </div>
      <div className="action-dock" aria-label="Hành động chính">
        <button className="primary-button" disabled={!canStart} onClick={onStart} type="button">
          Chạy
        </button>
        <button className="secondary-button" disabled={!canStop} onClick={onStop} type="button">
          Dừng
        </button>
        <button className="ghost-button" disabled={isBusy} onClick={onUpdateCheck} type="button">
          Kiểm tra bản mới
        </button>
      </div>
    </section>
  )
}

function MetricCard({
  label,
  value,
  detail,
  tone,
}: {
  label: string
  value: string
  detail: string
  tone: ConnectorStatus | 'neutral'
}) {
  return (
    <article className={`metric-card metric-${tone}`}>
      <p>{label}</p>
      <strong>{value}</strong>
      <span>{detail}</span>
    </article>
  )
}

function PairingPanel({
  pairingCode,
  errorMessage,
  canPair,
  isPaired,
  onChangePairingCode,
  onSubmit,
}: {
  pairingCode: string
  errorMessage: string
  canPair: boolean
  isPaired: boolean
  onChangePairingCode: (value: string) => void
  onSubmit: (event: FormEvent<HTMLFormElement>) => void
}) {
  return (
    <form className="surface-card pairing-panel" onSubmit={onSubmit}>
      <PanelHeader eyebrow="Pairing" title="Kết nối dashboard" meta={isPaired ? 'Đã ghép máy' : 'Nhập mã'} />
      <label className="field-label" htmlFor="pairing-code">
        Mã kết nối
      </label>
      <div className="pairing-row">
        <input
          id="pairing-code"
          className="pairing-input"
          value={pairingCode}
          placeholder="ABC123"
          autoComplete="one-time-code"
          onChange={(event) => onChangePairingCode(event.target.value.toUpperCase())}
        />
        <button className="primary-button" disabled={!canPair} type="submit">
          Kết nối
        </button>
      </div>
      <p className="microcopy">Lấy mã tại trang Kết nối trên dashboard cloud.</p>
      {errorMessage ? <p className="error-message">{errorMessage}</p> : null}
    </form>
  )
}

function RuntimePanel({
  status,
  updaterEvent,
  appVersion,
  isBusy,
  canStart,
  canStop,
  onStart,
  onStop,
  onUpdateCheck,
}: {
  status: ConnectorStatus
  updaterEvent: UpdaterEvent
  appVersion: string
  isBusy: boolean
  canStart: boolean
  canStop: boolean
  onStart: () => void
  onStop: () => void
  onUpdateCheck: () => void
}) {
  return (
    <section className="surface-card runtime-panel">
      <PanelHeader eyebrow="Runtime" title="Điều khiển connector" meta={STATUS_LABELS[status]} />
      <div className="runtime-actions">
        <button className="secondary-button" disabled={!canStart} onClick={onStart} type="button">
          Chạy connector
        </button>
        <button className="danger-button" disabled={!canStop} onClick={onStop} type="button">
          Dừng
        </button>
      </div>
      <div className="update-strip">
        <div>
          <p className="kicker">Update</p>
          <strong>{UPDATER_LABELS[updaterEvent.status] ?? updaterEvent.status}</strong>
          <span>v{appVersion}</span>
        </div>
        <StatusDot status={updaterEvent.status === 'error' ? 'error' : status} />
      </div>
      {updaterEvent.percent ? <ProgressBar percent={updaterEvent.percent} /> : null}
      <button className="ghost-button align-start" disabled={isBusy} onClick={onUpdateCheck} type="button">
        Kiểm tra bản mới
      </button>
    </section>
  )
}

function ActivityTimeline({ events, totalEvents }: { events: SidecarEvent[]; totalEvents: number }) {
  return (
    <section className="surface-card timeline-panel">
      <PanelHeader eyebrow="Timeline" title="Hoạt động gần đây" meta={`${totalEvents} events`} />
      <div className="timeline-list" aria-live="polite">
        {events.length > 0 ? (
          events.map((event, index) => <TimelineItem event={event} key={`${event.type}-${event.message}-${index}`} />)
        ) : (
          <p className="empty-log">Chưa có hoạt động. Kết nối máy để bắt đầu.</p>
        )}
      </div>
    </section>
  )
}

function PanelHeader({ eyebrow, title, meta }: { eyebrow: string; title: string; meta: string }) {
  return (
    <div className="panel-header">
      <div>
        <p className="kicker">{eyebrow}</p>
        <h3>{title}</h3>
      </div>
      <span>{meta}</span>
    </div>
  )
}

function StatusPill({ status }: { status: ConnectorStatus }) {
  return (
    <div className={`status-pill status-${status}`}>
      <StatusDot status={status} />
      {STATUS_LABELS[status]}
    </div>
  )
}

function StatusDot({ status }: { status: ConnectorStatus }) {
  return <span className={`status-dot status-${status}`} aria-hidden="true" />
}

function ProgressBar({ percent }: { percent: number }) {
  const safePercent = Math.max(0, Math.min(100, percent))
  return (
    <div className="progress-track" aria-label={`Đã tải ${Math.round(safePercent)}%`}>
      <span style={{ transform: `scaleX(${safePercent / 100})` }} />
    </div>
  )
}

function TimelineItem({ event }: { event: SidecarEvent }) {
  return (
    <article className={`timeline-item log-${event.level}`}>
      <span className="timeline-marker" />
      <div>
        <p>{event.message}</p>
        <span>{event.type}</span>
      </div>
    </article>
  )
}

function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message
  }
  return 'Không thể hoàn tất thao tác.'
}
