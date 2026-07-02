import { BrowserWindow, Menu, Tray, nativeImage } from 'electron'
import { checkForUpdatesSafely } from './updater.js'
import { SidecarProcessManager } from './sidecarProcess.js'

let tray: Tray | null = null

export function createConnectorTray(
  mainWindow: BrowserWindow,
  sidecar: SidecarProcessManager,
  quitApp: () => void,
): Tray {
  const image = nativeImage.createFromDataURL(
    'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA4AAAAOCAYAAAAfSC3RAAAAAXNSR0IArs4c6QAAAKlJREFUOE+dkjEOwjAMRZ9SuwJHYGJj6BhcABuwMzD0FDaegA2JQzChC7CxMRGqgNRQpCZRyQH5/vmTnF8B8Gvnp2vdgCXkq9zMPDAX6+6Ba1mbAs45MwBfDq1B5wQvYkEfsQJ0L4GLyJkRO4C5zJ3HQdm2G3CiFcWcTFbRO0m2bSE6AB0iVWR6glxUuxskYr5Kr4mI0TTVPG7hSp2ruj5te8K4H7b26xM+V38B2mU4ZHEmAAAAAElFTkSuQmCC',
  )
  tray = new Tray(image)
  tray.setToolTip('Facebook Group Connector')
  tray.setContextMenu(buildMenu(mainWindow, sidecar, quitApp))
  tray.on('click', () => showWindow(mainWindow))
  return tray
}

export function refreshTrayMenu(
  mainWindow: BrowserWindow,
  sidecar: SidecarProcessManager,
  quitApp: () => void,
): void {
  tray?.setContextMenu(buildMenu(mainWindow, sidecar, quitApp))
}

function buildMenu(
  mainWindow: BrowserWindow,
  sidecar: SidecarProcessManager,
  quitApp: () => void,
): Menu {
  const state = sidecar.getState()
  const canStart = state.status === 'offline' || state.status === 'error'
  const canStop = state.status === 'connecting' || state.status === 'online'

  return Menu.buildFromTemplate([
    { label: 'Open', click: () => showWindow(mainWindow) },
    { type: 'separator' },
    { label: 'Start connector', enabled: canStart, click: () => sidecar.startConnector() },
    { label: 'Stop connector', enabled: canStop, click: () => sidecar.stopConnector() },
    { type: 'separator' },
    { label: 'Check for updates', click: () => void checkForUpdatesSafely() },
    { type: 'separator' },
    { label: 'Quit', click: quitApp },
  ])
}

function showWindow(mainWindow: BrowserWindow): void {
  if (mainWindow.isMinimized()) {
    mainWindow.restore()
  }
  mainWindow.show()
  mainWindow.focus()
}
