import { BrowserWindow, dialog } from 'electron'
import { autoUpdater } from 'electron-updater'

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

export function configureAutoUpdater(mainWindow: BrowserWindow): void {
  autoUpdater.autoDownload = true
  autoUpdater.on('checking-for-update', () => {
    sendUpdaterEvent(mainWindow, {
      status: 'checking',
      message: 'Đang kiểm tra bản cập nhật...',
    })
  })
  autoUpdater.on('update-available', (info) => {
    sendUpdaterEvent(mainWindow, {
      status: 'available',
      message: `Có bản cập nhật ${info.version}, đang tải xuống...`,
      version: info.version,
    })
  })
  autoUpdater.on('update-not-available', (info) => {
    sendUpdaterEvent(mainWindow, {
      status: 'not_available',
      message: `Bạn đang dùng bản mới nhất (${info.version}).`,
      version: info.version,
    })
  })
  autoUpdater.on('download-progress', (progress) => {
    sendUpdaterEvent(mainWindow, {
      status: 'downloading',
      message: `Đang tải bản cập nhật ${Math.round(progress.percent)}%...`,
      percent: progress.percent,
    })
  })
  autoUpdater.on('update-downloaded', (info) => {
    sendUpdaterEvent(mainWindow, {
      status: 'downloaded',
      message: `Bản cập nhật ${info.version} đã sẵn sàng để cài đặt.`,
      version: info.version,
    })
    void promptForRestart()
  })
  autoUpdater.on('error', (error) => {
    sendUpdaterEvent(mainWindow, {
      status: 'error',
      message: `Không kiểm tra được cập nhật: ${error.message}`,
    })
  })
}

export async function checkForUpdatesSafely(): Promise<void> {
  try {
    await autoUpdater.checkForUpdates()
  } catch {
    return
  }
}

function sendUpdaterEvent(mainWindow: BrowserWindow, event: UpdaterEvent): void {
  mainWindow.webContents.send('updater:event', event)
}

async function promptForRestart(): Promise<void> {
  const result = await dialog.showMessageBox({
    type: 'info',
    buttons: ['Khởi động lại', 'Để sau'],
    defaultId: 0,
    cancelId: 1,
    title: 'Cập nhật Facebook Group Connector',
    message: 'Bản cập nhật đã tải xong. Khởi động lại app để cài đặt?',
  })

  if (result.response === 0) {
    autoUpdater.quitAndInstall()
  }
}
