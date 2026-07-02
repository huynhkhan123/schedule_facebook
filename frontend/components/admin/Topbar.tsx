import { StatusBadge } from '@/components/admin/StatusBadge'

export function Topbar() {
  return (
    <header className="sticky top-0 z-10 flex h-16 items-center justify-between border-b border-octo-border bg-octo-surface/95 px-4 backdrop-blur md:px-6">
      <div className="min-w-0">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-octo-neutral">Bảng điều khiển local</p>
        <h1 className="truncate text-lg font-semibold tracking-[-0.02em] text-octo-text-primary">Quản trị đăng nhóm an toàn</h1>
      </div>
      <div className="hidden items-center gap-3 md:flex">
        <label className="flex h-8 min-w-72 items-center gap-2 rounded-octo border border-octo-border bg-octo-background px-3 text-sm text-octo-text-secondary">
          <span>Tìm kiếm nhóm, chiến dịch...</span>
          <kbd className="ml-auto rounded-[3px] border border-octo-border px-1.5 py-0.5 font-mono text-[11px] text-octo-neutral">/</kbd>
        </label>
        <StatusBadge status="idle" />
      </div>
    </header>
  )
}
