'use client'

import { useRouter } from 'next/navigation'
import { useState } from 'react'
import { Button } from '@/components/admin/Button'
import { StatusBadge, statusLabel } from '@/components/admin/StatusBadge'
import type { SyncResponse } from '@/lib/api/types'

type GroupSyncControlsProps = {
  initialStatus: SyncResponse
}

const actions = [
  { label: 'Bắt đầu đồng bộ', endpoint: '/api/backend/automation/group-sync/start', variant: 'primary' as const },
  { label: 'Thu thập nhóm đang hiển thị', endpoint: '/api/backend/automation/group-sync/collect-visible', variant: 'outline' as const },
  { label: 'Dừng đồng bộ', endpoint: '/api/backend/automation/group-sync/stop', variant: 'danger' as const },
]

async function postSyncAction(endpoint: string): Promise<SyncResponse> {
  const response = await fetch(endpoint, { method: 'POST' })
  if (!response.ok) {
    throw new Error('Không kết nối được backend FastAPI')
  }

  return (await response.json()) as SyncResponse
}

export function GroupSyncControls({ initialStatus }: GroupSyncControlsProps) {
  const router = useRouter()
  const [status, setStatus] = useState(initialStatus)
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const runAction = async (endpoint: string): Promise<void> => {
    setError('')
    setIsLoading(true)
    try {
      const result = await postSyncAction(endpoint)
      setStatus(result)
      if (endpoint.endsWith('collect-visible')) {
        router.refresh()
      }
    } catch (syncError: unknown) {
      setError(syncError instanceof Error ? syncError.message : 'Không kết nối được backend FastAPI')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        {actions.map((action) => (
          <Button key={action.endpoint} type="button" variant={action.variant} disabled={isLoading} onClick={() => void runAction(action.endpoint)}>
            {action.label}
          </Button>
        ))}
      </div>
      <div className="flex flex-wrap items-center gap-3 rounded-octo border border-octo-border bg-octo-background px-3 py-2">
        <StatusBadge status={status.status} />
        <span className="font-mono text-xs text-octo-text-secondary">{status.synced_count} nhóm</span>
        <span className="text-sm text-octo-text-secondary">{status.message || statusLabel[status.status] || status.status}</span>
      </div>
      {error && <p className="rounded-octo border border-octo-error/40 bg-octo-error/10 px-3 py-2 text-sm text-octo-error">{error}</p>}
    </div>
  )
}
