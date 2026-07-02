import { BrowserWindow, dialog } from 'electron'
import { autoUpdater } from 'electron-updater'

export function configureAutoUpdater(mainWindow: BrowserWindow): void {
  autoUpdater.autoDownload = true
  autoUpdater.on('update-available', () => {
    mainWindow.webContents.send('updater:event', 'Có bản cập nhật mới, đang tải xuống...')
  })
  autoUpdater.on('update-downloaded', () => {
    mainWindow.webContents.send('updater:event', 'Bản cập nhật đã sẵn sàng để cài đặt.')
    void promptForRestart()
  })
  autoUpdater.on('error', (error) => {
    mainWindow.webContents.send('updater:event', `Không kiểm tra được cập nhật: ${error.message}`)
  })
}

export async function checkForUpdatesSafely(): Promise<void> {
  try {
    await autoUpdater.checkForUpdates()
  } catch {
    return
  }
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
