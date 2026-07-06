import { StatusBadge } from '@/components/admin/StatusBadge'

export function Topbar() {
  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-octo-border/80 bg-octo-surface/88 px-4 shadow-[0_16px_48px_rgb(1_4_9/22%)] backdrop-blur-xl md:px-6">
      <div className="min-w-0">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-octo-neutral">Bảng điều khiển local</p>
        <h1 className="truncate text-lg font-semibold tracking-[-0.02em] text-octo-text-primary">Quản trị đăng nhóm an toàn</h1>
      </div>
      <div className="hidden items-center gap-3 md:flex">
        <label className="flex h-8 min-w-72 items-center gap-2 rounded-octo border border-octo-border/90 bg-octo-background/72 px-3 text-sm text-octo-text-secondary shadow-inner">
          <span>Tìm kiếm nhóm, chiến dịch...</span>
          <kbd className="ml-auto rounded-[3px] border border-octo-border px-1.5 py-0.5 font-mono text-[11px] text-octo-neutral">/</kbd>
        </label>
        <StatusBadge status="idle" />
      </div>
    </header>
  )
}
