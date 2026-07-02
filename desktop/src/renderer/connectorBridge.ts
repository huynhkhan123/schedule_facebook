export type ConnectorStatus = 'offline' | 'pairing' | 'connecting' | 'online' | 'stopping' | 'error'

export interface SidecarEvent {
  type: string
  level: 'info' | 'warning' | 'error'
  message: string
  payload: Record<string, unknown>
}

export interface ConnectorState {
  status: ConnectorStatus
  logs: SidecarEvent[]
  isPaired: boolean
  errorMessage: string
}

export type UpdaterStatus =
  | 'idle'
  | 'checking'
  | 'available'
  | 'not_available'
  | 'downloading'
  | 'downloaded'
  | 'error'

export interface UpdaterEvent {
  status: UpdaterStatus
  message: string
  version?: string
  percent?: number
}

export interface ConnectorBridge {
  getAppVersion: () => Promise<string>
  getState: () => Promise<ConnectorState>
  pairConnector: (code: string) => Promise<ConnectorState>
  startConnector: () => Promise<ConnectorState>
  stopConnector: () => Promise<ConnectorState>
  checkForUpdates: () => Promise<void>
  onState: (callback: (state: ConnectorState) => void) => () => void
  onUpdaterEvent: (callback: (event: UpdaterEvent) => void) => () => void
}

declare global {
  interface Window {
    connector: ConnectorBridge
  }
}
