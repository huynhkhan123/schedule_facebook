import { AdminTable } from '@/components/admin/AdminTable'
import { Callout } from '@/components/admin/Callout'
import { EmptyState } from '@/components/admin/EmptyState'
import { GroupSyncControls } from '@/components/admin/GroupSyncControls'
import { OpenGroupButton } from '@/components/admin/OpenGroupButton'
import { PageHeader } from '@/components/admin/PageHeader'
import { Pagination } from '@/components/admin/Pagination'
import { Panel } from '@/components/admin/Panel'
import { StatusBadge } from '@/components/admin/StatusBadge'
import { fetchBackend } from '@/lib/api/client'
import type { Group, SyncResponse } from '@/lib/api/types'

type GroupsPageProps = {
  searchParams?: Promise<{
    page?: string
    limit?: string
  }>
}

const DEFAULT_PAGE = 1
const DEFAULT_PAGE_SIZE = 20
const PAGE_SIZE_OPTIONS = new Set([10, 20, 50])

async function loadGroups(): Promise<Group[]> {
  try {
    return await fetchBackend<Group[]>('/api/groups')
  } catch {
    return []
  }
}

async function loadSyncStatus(): Promise<SyncResponse> {
  try {
    return await fetchBackend<SyncResponse>('/api/automation/group-sync/status')
  } catch {
    return { status: 'error', synced_count: 0, message: 'Không kết nối được backend FastAPI' }
  }
}

function parsePositiveInteger(value: string | undefined, fallback: number): number {
  if (!value) {
    return fallback
  }

  const parsed = Number.parseInt(value, 10)
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback
}

function getPaginationState(groups: Group[], pageParam: string | undefined, limitParam: string | undefined) {
  const requestedPage = parsePositiveInteger(pageParam, DEFAULT_PAGE)
  const requestedLimit = parsePositiveInteger(limitParam, DEFAULT_PAGE_SIZE)
  const pageSize = PAGE_SIZE_OPTIONS.has(requestedLimit) ? requestedLimit : DEFAULT_PAGE_SIZE
  const totalItems = groups.length
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize))
  const currentPage = Math.min(requestedPage, totalPages)
  const startIndex = (currentPage - 1) * pageSize
  const endIndex = Math.min(startIndex + pageSize, totalItems)

  return {
    currentPage,
    pageSize,
    totalItems,
    totalPages,
    visibleGroups: groups.slice(startIndex, endIndex),
  }
}

export default async function GroupsPage({ searchParams }: GroupsPageProps) {
  const resolvedSearchParams = await searchParams
  const [groups, syncStatus] = await Promise.all([loadGroups(), loadSyncStatus()])
  const { currentPage, pageSize, totalItems, totalPages, visibleGroups } = getPaginationState(
    groups,
    resolvedSearchParams?.page,
    resolvedSearchParams?.limit,
  )

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Human-in-the-loop"
        title="Quản lý nhóm"
        description="Đồng bộ nhóm bằng browser local, duyệt danh sách gọn hơn và mở nhóm trong profile connector."
      />

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1.2fr)_minmax(20rem,0.8fr)]">
        <Panel title="Đồng bộ nhóm" eyebrow="Trình duyệt Playwright">
          <GroupSyncControls initialStatus={syncStatus} />
        </Panel>
        <Callout title="Luồng đúng" tone="warning">
          <ol className="list-decimal space-y-1 pl-5 text-octo-text-primary">
            <li>Bắt đầu đồng bộ.</li>
            <li>Đăng nhập và cuộn trong browser connector.</li>
            <li>Thu thập nhóm đang hiển thị.</li>
            <li>Dừng connector khi hoàn tất.</li>
          </ol>
        </Callout>
      </div>

      <Panel title="Danh sách nhóm đã đồng bộ" eyebrow={`${groups.length} nhóm`} className="p-0">
        {groups.length === 0 ? (
          <div className="p-4">
            <EmptyState
              title="Chưa có nhóm nào được đồng bộ"
              description="Bắt đầu sync, cuộn trong browser được tool mở, rồi thu thập các nhóm đang hiển thị để bảng này có dữ liệu."
            />
          </div>
        ) : (
          <>
            <div className="px-4 pb-4">
              <AdminTable headers={['Tên nhóm', 'Facebook', 'Đang bật', 'Được phép đăng', 'Ghi chú']}>
                {visibleGroups.map((group) => (
                  <tr key={group.id} className="group hover:bg-octo-elevated/90">
                    <td className="max-w-[28rem] px-4 py-3 font-medium text-octo-text-primary">
                      <span className="line-clamp-2 transition-colors group-hover:text-white">{group.name}</span>
                    </td>
                    <td className="px-4 py-3">
                      <OpenGroupButton url={group.url} />
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
            </div>
            <Pagination basePath="/nhom" currentPage={currentPage} totalPages={totalPages} pageSize={pageSize} totalItems={totalItems} />
          </>
        )}
      </Panel>
    </div>
  )
}
