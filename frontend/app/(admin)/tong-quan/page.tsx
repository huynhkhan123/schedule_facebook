import Link from 'next/link'
import { Callout } from '@/components/admin/Callout'
import { PageHeader } from '@/components/admin/PageHeader'
import { Panel } from '@/components/admin/Panel'
import { StatCard } from '@/components/admin/StatCard'
import { fetchBackend } from '@/lib/api/client'
import type { Group } from '@/lib/api/types'

async function loadGroupCount() {
  try {
    const groups = await fetchBackend<Group[]>('/api/groups')
    return groups.length
  } catch {
    return 0
  }
}

export default async function OverviewPage() {
  const syncedGroups = await loadGroupCount()

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Octo Code Admin"
        title="Tổng quan vận hành"
        description="Theo dõi trạng thái đồng bộ nhóm, mức sử dụng automation và những việc cần bạn xử lý thủ công trước khi chạy campaign."
        actions={
          <Link href="/nhom" className="inline-flex h-8 items-center rounded-octo border border-octo-secondary bg-octo-secondary px-4 text-sm font-medium text-white hover:bg-octo-success">
            Mở đồng bộ nhóm
          </Link>
        }
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Nhóm đã đồng bộ" value={syncedGroups} description="Tổng số nhóm backend đang trả về" tone="blue" />
        <StatCard label="Chiến dịch đang chạy" value={0} description="Chưa bật campaign tự động trong phase UI này" tone="green" />
        <StatCard label="Lượt auto hôm nay" value={0} description="Giới hạn cứng vẫn do backend kiểm soát" tone="yellow" />
        <StatCard label="Cần xử lý" value={0} description="Checkpoint/login/CAPTCHA sẽ yêu cầu bạn thao tác" tone="red" />
      </div>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(20rem,0.8fr)]">
        <Panel title="Nhật ký vận hành gần đây" eyebrow="Activity feed">
          <div className="space-y-3">
            {['Dashboard Next.js đã sẵn sàng', 'Workflow sync nhóm dùng browser riêng', 'Jinja dashboard cũ vẫn giữ làm fallback'].map((item) => (
              <div key={item} className="flex items-start gap-3 rounded-octo border border-octo-border bg-octo-background p-3">
                <span className="mt-1 h-2 w-2 rounded-full bg-octo-success" />
                <div>
                  <p className="text-sm font-medium text-octo-text-primary">{item}</p>
                  <p className="mt-1 font-mono text-xs text-octo-text-secondary">local.admin.event</p>
                </div>
              </div>
            ))}
          </div>
        </Panel>

        <Callout title="Giới hạn an toàn" tone="warning">
          <ul className="list-disc space-y-2 pl-5">
            <li>Không lưu mật khẩu hoặc credential Facebook trong dashboard.</li>
            <li>Không bypass checkpoint, CAPTCHA hoặc xác minh bảo mật.</li>
            <li>Auto mode giữ giới hạn 1–20 nhóm/ngày và cần dry-run.</li>
            <li>Semi-auto chuẩn bị bài viết, bạn là người xác nhận đăng.</li>
          </ul>
        </Callout>
      </div>
    </div>
  )
}
