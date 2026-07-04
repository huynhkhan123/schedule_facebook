'use client'

import { useState } from 'react'
import { Button } from '@/components/admin/Button'
import { getPublicBackendApiUrl } from '@/lib/api/client'

type OpenGroupButtonProps = {
  url: string
}

export function OpenGroupButton({ url }: OpenGroupButtonProps) {
  const [error, setError] = useState('')
  const [isOpening, setIsOpening] = useState(false)

  const openGroup = async (): Promise<void> => {
    setError('')
    setIsOpening(true)
    try {
      const response = await fetch(getPublicBackendApiUrl('/api/automation/groups/open'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      })
      if (!response.ok) {
        throw new Error('Không gửi được lệnh mở nhóm xuống desktop connector')
      }
    } catch (openError: unknown) {
      setError(openError instanceof Error ? openError.message : 'Không gửi được lệnh mở nhóm xuống desktop connector')
    } finally {
      setIsOpening(false)
    }
  }

  return (
    <div className="space-y-1">
      <Button type="button" variant="outline" disabled={isOpening} onClick={() => void openGroup()} className="font-mono text-xs">
        {isOpening ? 'Đang mở...' : 'Mở nhóm'}
      </Button>
      {error && <p className="max-w-48 text-xs text-octo-error">{error}</p>}
    </div>
  )
}
