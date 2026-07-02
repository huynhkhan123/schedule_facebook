import { Callout } from '@/components/admin/Callout'
import { EmptyState } from '@/components/admin/EmptyState'
import { PageHeader } from '@/components/admin/PageHeader'
import { PairingCodeButton } from '@/components/admin/PairingCodeButton'
import { Panel } from '@/components/admin/Panel'
import { StatusBadge } from '@/components/admin/StatusBadge'
import { fetchBackend } from '@/lib/api/client'
import type { Connector } from '@/lib/api/types'

async function loadConnectors() {
  try {
    return await fetchBackend<Connector[]>('/api/connectors')
  } catch {
    return []
  }
}

export default async function ConnectorsPage() {
  const connectors = await loadConnectors()

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Local runner"
        title="Kết nối máy cục bộ"
        description="Ghép dashboard cloud với desktop connector chạy trên máy khách để browser Facebook mở local, không chạy trong Azure."
      />

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(20rem,0.8fr)]">
        <Panel title="Pair desktop connector" eyebrow="Mã kết nối">
          <PairingCodeButton />
        </Panel>
        <Callout title="Cách chạy connector" tone="info">
          <pre className="overflow-x-auto rounded-octo bg-octo-background p-3 font-mono text-xs text-octo-text-primary">
{`python3 -m uv run facebook-group-connector pair \\
  --code <CODE> \\
  --server https://schedule.bookinghome.one

python3 -m uv run facebook-group-connector run`}
          </pre>
        </Callout>
      </div>

      <Panel title="Connector đã ghép" eyebrow={`${connectors.length} máy`}>
        {connectors.length === 0 ? (
          <EmptyState
            title="Chưa có máy cục bộ nào kết nối"
            description="Tạo mã kết nối, mở desktop connector trên máy khách và nhập mã để dashboard có thể gửi job sync/post xuống local runner."
          />
        ) : (
          <div className="space-y-2">
            {connectors.map((connector) => (
              <div key={connector.id} className="rounded-octo border border-octo-border bg-octo-background p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="font-medium text-octo-text-primary">{connector.machine_name}</p>
                    <p className="font-mono text-xs text-octo-text-secondary">{connector.platform}</p>
                  </div>
                  <StatusBadge status={connector.status === 'online' ? 'syncing_visible_groups' : 'stopped'} />
                </div>
                <p className="mt-3 text-sm text-octo-text-secondary">
                  Capabilities: {connector.capabilities.join(', ') || 'chưa khai báo'}
                </p>
              </div>
            ))}
          </div>
        )}
      </Panel>
    </div>
  )
}
