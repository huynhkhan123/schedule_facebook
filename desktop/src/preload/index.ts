import { contextBridge, ipcRenderer } from 'electron'

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

const connectorBridge: ConnectorBridge = {
  getState: () => ipcRenderer.invoke('connector:getState') as Promise<ConnectorState>,
  pairConnector: (code: string) => ipcRenderer.invoke('connector:pair', code) as Promise<ConnectorState>,
  startConnector: () => ipcRenderer.invoke('connector:start') as Promise<ConnectorState>,
  stopConnector: () => ipcRenderer.invoke('connector:stop') as Promise<ConnectorState>,
  checkForUpdates: () => ipcRenderer.invoke('updater:check') as Promise<void>,
  onState: (callback: (state: ConnectorState) => void) => {
    const listener = (_event: Electron.IpcRendererEvent, state: ConnectorState) => callback(state)
    ipcRenderer.on('connector:state', listener)
    return () => ipcRenderer.removeListener('connector:state', listener)
  },
  onUpdaterEvent: (callback: (message: string) => void) => {
    const listener = (_event: Electron.IpcRendererEvent, message: string) => callback(message)
    ipcRenderer.on('updater:event', listener)
    return () => ipcRenderer.removeListener('updater:event', listener)
  },
}

contextBridge.exposeInMainWorld('connector', connectorBridge)
