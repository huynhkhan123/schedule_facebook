import { EventEmitter } from 'node:events'
import { existsSync } from 'node:fs'
import path from 'node:path'
import { ChildProcessWithoutNullStreams, spawn } from 'node:child_process'
import { app } from 'electron'

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

const DEFAULT_SERVER_URL = 'https://schedule.bookinghome.one'
const MAX_LOG_LINES = 200

export class SidecarProcessManager extends EventEmitter {
  private runProcess: ChildProcessWithoutNullStreams | null = null
  private state: ConnectorState = {
    status: 'offline',
    logs: [],
    isPaired: false,
    errorMessage: '',
  }

  getState(): ConnectorState {
    return {
      ...this.state,
      logs: [...this.state.logs],
    }
  }

  async pairConnector(code: string): Promise<ConnectorState> {
    const normalizedCode = code.trim()
    if (!normalizedCode) {
      this.setError('Vui lòng nhập mã kết nối từ dashboard.')
      return this.getState()
    }

    this.setStatus('pairing')
    await this.runOneShot(['pair', '--code', normalizedCode, '--server', DEFAULT_SERVER_URL])
    this.state = {
      ...this.state,
      isPaired: true,
      status: 'offline',
      errorMessage: '',
    }
    this.emitState()
    return this.getState()
  }

  startConnector(): ConnectorState {
    if (this.runProcess) {
      this.pushLog({
        type: 'already_running',
        level: 'info',
        message: 'Connector đang chạy.',
        payload: {},
      })
      return this.getState()
    }

    this.setStatus('connecting')
    const child = spawnSidecar(['run'])
    this.runProcess = child

    child.stdout.on('data', (chunk: Buffer) => {
      this.handleOutput(chunk)
      if (this.state.status === 'connecting') {
        this.setStatus('online')
      }
    })

    child.stderr.on('data', (chunk: Buffer) => {
      this.pushLog({
        type: 'stderr',
        level: 'error',
        message: chunk.toString('utf8').trim(),
        payload: {},
      })
      this.setStatus('error')
    })

    child.on('exit', (code) => {
      this.runProcess = null
      if (this.state.status === 'stopping') {
        this.setStatus('offline')
        return
      }
      if (code === 0) {
        this.setStatus('offline')
        return
      }
      this.setError(`Connector đã dừng bất thường với mã ${code ?? 'unknown'}.`)
    })

    return this.getState()
  }

  stopConnector(): ConnectorState {
    if (!this.runProcess) {
      this.setStatus('offline')
      return this.getState()
    }

    this.setStatus('stopping')
    this.runProcess.kill('SIGTERM')
    return this.getState()
  }

  async stopBeforeQuit(): Promise<void> {
    if (!this.runProcess) {
      return
    }

    await new Promise<void>((resolve) => {
      const child = this.runProcess
      if (!child) {
        resolve()
        return
      }
      child.once('exit', () => resolve())
      child.kill('SIGTERM')
      setTimeout(resolve, 3000)
    })
  }

  private async runOneShot(args: string[]): Promise<void> {
    await new Promise<void>((resolve, reject) => {
      const child = spawnSidecar(args)

      child.stdout.on('data', (chunk: Buffer) => this.handleOutput(chunk))
      child.stderr.on('data', (chunk: Buffer) => {
        this.pushLog({
          type: 'stderr',
          level: 'error',
          message: chunk.toString('utf8').trim(),
          payload: {},
        })
      })
      child.on('error', reject)
      child.on('exit', (code) => {
        if (code === 0) {
          resolve()
          return
        }
        reject(new Error(`Sidecar exited with code ${code ?? 'unknown'}`))
      })
    }).catch((error: unknown) => {
      const message = error instanceof Error ? error.message : 'Không chạy được connector sidecar.'
      this.setError(message)
      throw error
    })
  }

  private handleOutput(chunk: Buffer): void {
    const lines = chunk.toString('utf8').split('\n').filter(Boolean)
    for (const line of lines) {
      this.pushLog(parseSidecarEvent(line))
    }
  }

  private pushLog(event: SidecarEvent): void {
    this.state = {
      ...this.state,
      logs: [...this.state.logs, event].slice(-MAX_LOG_LINES),
      errorMessage: event.level === 'error' ? event.message : this.state.errorMessage,
    }
    this.emitState()
  }

  private setStatus(status: ConnectorStatus): void {
    this.state = {
      ...this.state,
      status,
      errorMessage: status === 'error' ? this.state.errorMessage : '',
    }
    this.emitState()
  }

  private setError(message: string): void {
    this.state = {
      ...this.state,
      status: 'error',
      errorMessage: message,
    }
    this.pushLog({ type: 'error', level: 'error', message, payload: {} })
    this.emitState()
  }

  private emitState(): void {
    this.emit('state', this.getState())
  }
}

interface SidecarCommand {
  executable: string
  prefixArgs: string[]
}

function spawnSidecar(args: string[]): ChildProcessWithoutNullStreams {
  const command = resolveSidecarCommand()
  return spawn(command.executable, [...command.prefixArgs, ...args], {
    cwd: resolveProjectRoot(),
    env: {
      ...process.env,
      PLAYWRIGHT_BROWSERS_PATH: resolvePlaywrightBrowsersPath(),
      PYTHONUNBUFFERED: '1',
    },
  })
}

function resolveSidecarCommand(): SidecarCommand {
  if (process.env.CONNECTOR_SIDECAR_COMMAND) {
    return { executable: process.env.CONNECTOR_SIDECAR_COMMAND, prefixArgs: [] }
  }

  const packagedExecutable = path.join(process.resourcesPath, 'sidecar', sidecarExecutableName())
  if (app.isPackaged && existsSync(packagedExecutable)) {
    return { executable: packagedExecutable, prefixArgs: [] }
  }

  const projectRoot = resolveProjectRoot()
  const venvPython = resolveVenvPython(projectRoot)
  if (venvPython) {
    return {
      executable: venvPython,
      prefixArgs: ['-m', 'facebook_group_tool.connector.sidecar'],
    }
  }

  return {
    executable: process.platform === 'win32' ? 'python' : 'python3',
    prefixArgs: ['-m', 'facebook_group_tool.connector.sidecar'],
  }
}

function resolveProjectRoot(): string {
  return path.resolve(app.getAppPath(), '..')
}

function resolvePlaywrightBrowsersPath(): string {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'ms-playwright')
  }

  return path.join(resolveProjectRoot(), 'desktop', 'resources', 'ms-playwright')
}

function resolveVenvPython(projectRoot: string): string | null {
  const candidates =
    process.platform === 'win32'
      ? [path.join(projectRoot, '.venv', 'Scripts', 'python.exe')]
      : [path.join(projectRoot, '.venv', 'bin', 'python')]

  return candidates.find((candidate) => existsSync(candidate)) ?? null
}

function sidecarExecutableName(): string {
  return process.platform === 'win32' ? 'facebook-group-connector-sidecar.exe' : 'facebook-group-connector-sidecar'
}

function parseSidecarEvent(line: string): SidecarEvent {
  try {
    const parsed = JSON.parse(line) as Partial<SidecarEvent>
    return {
      type: typeof parsed.type === 'string' ? parsed.type : 'log',
      level: isLogLevel(parsed.level) ? parsed.level : 'info',
      message: typeof parsed.message === 'string' ? parsed.message : line,
      payload: isRecord(parsed.payload) ? parsed.payload : {},
    }
  } catch {
    return {
      type: 'log',
      level: 'info',
      message: line,
      payload: {},
    }
  }
}

function isLogLevel(value: unknown): value is SidecarEvent['level'] {
  return value === 'info' || value === 'warning' || value === 'error'
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}
