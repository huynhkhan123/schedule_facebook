type CalloutProps = {
  title: string
  children: React.ReactNode
  tone?: 'info' | 'warning' | 'danger'
}

const tones = {
  info: 'border-octo-primary/40 bg-octo-primary/10 text-octo-primary',
  warning: 'border-octo-warning/40 bg-octo-warning/10 text-octo-warning',
  danger: 'border-octo-error/40 bg-octo-error/10 text-octo-error',
}

export function Callout({ title, children, tone = 'info' }: CalloutProps) {
  return (
    <aside className={`rounded-octo border p-4 ${tones[tone]}`}>
      <p className="text-sm font-semibold">{title}</p>
      <div className="mt-2 text-sm leading-6 text-octo-text-primary">{children}</div>
    </aside>
  )
}
