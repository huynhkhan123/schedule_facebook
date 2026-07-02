import path from 'node:path'
import { BrowserWindow, app, ipcMain, shell } from 'electron'
import { SidecarProcessManager } from './sidecarProcess.js'
import { checkForUpdatesSafely, configureAutoUpdater } from './updater.js'
import { createConnectorTray, refreshTrayMenu } from './tray.js'

const sidecar = new SidecarProcessManager()
let mainWindow: BrowserWindow | null = null
let isQuitting = false

const singleInstanceLock = app.requestSingleInstanceLock()

if (!singleInstanceLock) {
  app.quit()
} else {
  app.on('second-instance', () => {
    if (!mainWindow) {
      return
    }
    if (mainWindow.isMinimized()) {
      mainWindow.restore()
    }
    mainWindow.show()
    mainWindow.focus()
  })

  app.whenReady().then(() => {
    mainWindow = createMainWindow()
    configureIpc()
    configureAutoUpdater(mainWindow)
    createConnectorTray(mainWindow, sidecar, quitApp)
    sidecar.on('state', () => {
      if (!mainWindow) {
        return
      }
      mainWindow.webContents.send('connector:state', sidecar.getState())
      refreshTrayMenu(mainWindow, sidecar, quitApp)
    })
    void checkForUpdatesSafely()
  })
}

app.on('window-all-closed', () => {
  // Keep the app alive in tray/background mode.
})

app.on('before-quit', () => {
  isQuitting = true
})

function createMainWindow(): BrowserWindow {
  const window = new BrowserWindow({
    width: 880,
    height: 680,
    minWidth: 760,
    minHeight: 600,
    title: 'Facebook Group Connector',
    backgroundColor: '#0d1117',
    show: false,
    titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default',
    webPreferences: {
      preload: path.join(__dirname, '../preload/index.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
  })

  window.once('ready-to-show', () => window.show())
  window.on('close', (event) => {
    if (isQuitting) {
      return
    }
    event.preventDefault()
    window.hide()
  })
  window.webContents.setWindowOpenHandler(({ url }) => {
    void shell.openExternal(url)
    return { action: 'deny' }
  })

  if (process.env.VITE_DEV_SERVER_URL) {
    void window.loadURL(process.env.VITE_DEV_SERVER_URL)
  } else {
    void window.loadFile(path.join(__dirname, '../renderer/index.html'))
  }

  return window
}

function configureIpc(): void {
  ipcMain.handle('connector:getState', () => sidecar.getState())
  ipcMain.handle('connector:pair', async (_event, code: string) => sidecar.pairConnector(code))
  ipcMain.handle('connector:start', () => sidecar.startConnector())
  ipcMain.handle('connector:stop', () => sidecar.stopConnector())
  ipcMain.handle('updater:check', async () => checkForUpdatesSafely())
}

function quitApp(): void {
  isQuitting = true
  void sidecar.stopBeforeQuit().finally(() => app.quit())
}
