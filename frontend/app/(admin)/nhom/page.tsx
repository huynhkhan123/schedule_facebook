import { AdminTable } from '@/components/admin/AdminTable'
import { Callout } from '@/components/admin/Callout'
import { EmptyState } from '@/components/admin/EmptyState'
import { GroupSyncControls } from '@/components/admin/GroupSyncControls'
import { PageHeader } from '@/components/admin/PageHeader'
import { Panel } from '@/components/admin/Panel'
import { StatusBadge } from '@/components/admin/StatusBadge'
import { fetchBackend } from '@/lib/api/client'
import type { Group, SyncResponse } from '@/lib/api/types'

async function loadGroups() {
  try {
    return await fetchBackend<Group[]>('/api/groups')
  } catch {
    return []
  }
}

async function loadSyncStatus() {
  try {
    return await fetchBackend<SyncResponse>('/api/automation/group-sync/status')
  } catch {
    return { status: 'error', synced_count: 0, message: 'Không kết nối được backend FastAPI' }
  }
}

export default async function GroupsPage() {
  const [groups, syncStatus] = await Promise.all([loadGroups(), loadSyncStatus()])

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Human-in-the-loop"
        title="Quản lý nhóm"
        description="Đồng bộ danh sách nhóm bằng browser do tool mở, sau đó quản lý nhóm nào được bật và nhóm nào được phép đăng. Tool không đọc tab Facebook bạn tự mở riêng."
      />

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1.2fr)_minmax(20rem,0.8fr)]">
        <Panel title="Đồng bộ nhóm" eyebrow="Trình duyệt Playwright">
          <GroupSyncControls initialStatus={syncStatus} />
        </Panel>
        <Callout title="Luồng đúng" tone="warning">
          <ol className="list-decimal space-y-1 pl-5 text-octo-text-primary">
            <li>Bấm “Bắt đầu đồng bộ”.</li>
            <li>Đăng nhập và cuộn trang trong browser do tool mở.</li>
            <li>Quay lại dashboard và bấm “Thu thập nhóm đang hiển thị”.</li>
            <li>Bấm “Dừng đồng bộ” khi hoàn tất.</li>
          </ol>
        </Callout>
      </div>

      <Panel title="Danh sách nhóm đã đồng bộ" eyebrow={`${groups.length} nhóm`}>
        {groups.length === 0 ? (
          <EmptyState
            title="Chưa có nhóm nào được đồng bộ"
            description="Bắt đầu sync, cuộn trong browser được tool mở, rồi thu thập các nhóm đang hiển thị để bảng này có dữ liệu."
          />
        ) : (
          <AdminTable headers={['Tên nhóm', 'Facebook', 'Đang bật', 'Được phép đăng', 'Ghi chú']}>
            {groups.map((group) => (
              <tr key={group.id} className="hover:bg-octo-elevated">
                <td className="px-4 py-3 font-medium text-octo-text-primary">{group.name}</td>
                <td className="px-4 py-3">
                  <a href={group.url} target="_blank" rel="noreferrer" className="font-mono text-xs text-octo-primary hover:text-octo-primary-hover">
                    Mở nhóm
                  </a>
                </td>
                <td className="px-4 py-3">
                  <StatusBadge status={group.is_enabled ? 'syncing_visible_groups' : 'stopped'} />
                </td>
                <td className="px-4 py-3">
                  <StatusBadge status={group.is_posting_allowed ? 'idle' : 'needs_user_action'} />
                </td>
                <td className="px-4 py-3 text-octo-text-secondary">{group.note || 'Chưa có ghi chú'}</td>
              </tr>
            ))}
          </AdminTable>
        )}
      </Panel>
    </div>
  )
}
