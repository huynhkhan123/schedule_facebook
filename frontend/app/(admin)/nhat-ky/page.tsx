import { EmptyState } from '@/components/admin/EmptyState'
import { PageHeader } from '@/components/admin/PageHeader'
import { Panel } from '@/components/admin/Panel'

export default function LogsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Audit trail"
        title="Nhật ký"
        description="Theo dõi các sự kiện sync, campaign, lỗi UI Facebook và các điểm cần bạn xử lý trong browser."
      />
      <Panel title="Dòng sự kiện" eyebrow="Run logs">
        <EmptyState
          title="Chưa có API đọc nhật ký trong dashboard mới"
          description="Phase sau nên thêm endpoint log listing/filtering để hiển thị dòng sự kiện đầy đủ bằng JetBrains Mono."
        />
      </Panel>
    </div>
  )
}
