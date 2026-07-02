'use client'

import { useState } from 'react'
import { Button } from '@/components/admin/Button'
import type { PairingCodeResponse } from '@/lib/api/types'

export function PairingCodeButton() {
  const [code, setCode] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const createCode = async (): Promise<void> => {
    setError('')
    setIsLoading(true)
    try {
      const response = await fetch('/api/backend/connectors/pairing-codes', { method: 'POST' })
      if (!response.ok) {
        throw new Error('Không tạo được mã kết nối')
      }
      const payload = (await response.json()) as PairingCodeResponse
      setCode(payload.code)
    } catch (pairingError: unknown) {
      setError(pairingError instanceof Error ? pairingError.message : 'Không tạo được mã kết nối')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-3">
      <Button type="button" disabled={isLoading} onClick={() => void createCode()}>
        Tạo mã kết nối
      </Button>
      {code && (
        <div className="rounded-octo border border-octo-primary/40 bg-octo-primary/10 p-4">
          <p className="text-sm text-octo-text-secondary">Nhập mã này vào desktop connector:</p>
          <p className="mt-2 font-mono text-3xl font-medium tracking-[0.12em] text-octo-primary">{code}</p>
        </div>
      )}
      {error && <p className="text-sm text-octo-error">{error}</p>}
    </div>
  )
}
