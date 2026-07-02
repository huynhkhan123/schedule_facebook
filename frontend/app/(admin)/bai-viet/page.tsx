import { EmptyState } from '@/components/admin/EmptyState'
import { PageHeader } from '@/components/admin/PageHeader'
import { Panel } from '@/components/admin/Panel'

export default function PostsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Content library"
        title="Bài viết"
        description="Quản lý bản nháp nội dung trước khi đưa vào campaign. Link/video sẽ được xử lý ở phase sau để tránh mở rộng automation quá sớm."
      />
      <Panel title="Thư viện bài viết" eyebrow="Đang chuẩn bị">
        <EmptyState
          title="Chưa có giao diện tạo bài viết trong dashboard mới"
          description="Backend đã có nền tảng tạo post; UI phase đầu tập trung hoàn thiện shell và workflow đồng bộ nhóm trước."
        />
      </Panel>
    </div>
  )
}
