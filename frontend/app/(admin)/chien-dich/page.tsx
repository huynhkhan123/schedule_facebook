import { EmptyState } from '@/components/admin/EmptyState'
import { PageHeader } from '@/components/admin/PageHeader'
import { Panel } from '@/components/admin/Panel'

export default function CampaignsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Scheduling"
        title="Chiến dịch"
        description="Theo dõi campaign auto/semi-auto, dry-run, giới hạn tốc độ và trạng thái cần người dùng xử lý."
      />
      <Panel title="Campaign queue" eyebrow="Safety-first">
        <EmptyState
          title="Chưa có campaign nào trong dashboard mới"
          description="Khi mở rộng màn hình này, mọi action chạy campaign vẫn phải đi qua backend safety guard và không được thêm bypass."
        />
      </Panel>
    </div>
  )
}
