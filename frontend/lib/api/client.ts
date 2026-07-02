export function getBackendBaseUrl() {
  return process.env.FASTAPI_BASE_URL ?? 'http://127.0.0.1:8000'
}

export function getPublicBackendBaseUrl() {
  return process.env.NEXT_PUBLIC_FASTAPI_BASE_URL ?? ''
}

export function getBackendApiUrl(path: string) {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  return `${getBackendBaseUrl()}${normalizedPath}`
}

export function getPublicBackendApiUrl(path: string) {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  return `${getPublicBackendBaseUrl()}${normalizedPath}`
}

export async function fetchBackend<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(getBackendApiUrl(path), {
    ...init,
    cache: 'no-store',
  })

  if (!response.ok) {
    throw new Error(`FastAPI request failed with status ${response.status}`)
  }

  return (await response.json()) as T
}
