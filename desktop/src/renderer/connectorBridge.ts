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

export interface ConnectorBridge {
  getState: () => Promise<ConnectorState>
  pairConnector: (code: string) => Promise<ConnectorState>
  startConnector: () => Promise<ConnectorState>
  stopConnector: () => Promise<ConnectorState>
  checkForUpdates: () => Promise<void>
  onState: (callback: (state: ConnectorState) => void) => () => void
  onUpdaterEvent: (callback: (message: string) => void) => () => void
}

declare global {
  interface Window {
    connector: ConnectorBridge
  }
}
