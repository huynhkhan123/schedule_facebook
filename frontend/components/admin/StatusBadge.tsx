const statusTone = {
  idle: 'border-octo-border text-octo-text-secondary bg-octo-elevated',
  opening_browser: 'border-octo-primary/40 text-octo-primary bg-octo-primary/10',
  waiting_for_user_scroll: 'border-octo-warning/40 text-octo-warning bg-octo-warning/10',
  syncing_visible_groups: 'border-octo-primary/40 text-octo-primary bg-octo-primary/10',
  needs_user_action: 'border-octo-error/40 text-octo-error bg-octo-error/10',
  stopped: 'border-octo-border text-octo-text-secondary bg-octo-elevated',
  error: 'border-octo-error/40 text-octo-error bg-octo-error/10',
} as const

const pulsingStatuses = new Set(['opening_browser', 'waiting_for_user_scroll', 'syncing_visible_groups'])

export const statusLabel: Record<string, string> = {
  idle: 'Đang chờ',
  opening_browser: 'Đang mở trình duyệt',
  waiting_for_user_scroll: 'Chờ bạn cuộn trang nhóm',
  syncing_visible_groups: 'Đang thu thập nhóm đang hiển thị',
  needs_user_action: 'Cần bạn xử lý trong trình duyệt',
  stopped: 'Đã dừng',
  error: 'Lỗi',
}

type StatusBadgeProps = {
  status: string
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const tone = status in statusTone ? statusTone[status as keyof typeof statusTone] : statusTone.idle
  const label = statusLabel[status] ?? status
  const shouldPulse = pulsingStatuses.has(status)

  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-1 font-mono text-xs shadow-[0_0_20px_rgb(1_4_9/16%)] ${tone}`}>
      <span className={`mr-1.5 h-1.5 w-1.5 rounded-full bg-current ${shouldPulse ? 'animate-pulse' : ''}`} />
      {label}
    </span>
  )
}
