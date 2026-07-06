type PageHeaderProps = {
  eyebrow: string
  title: string
  description: string
  actions?: React.ReactNode
}

export function PageHeader({ eyebrow, title, description, actions }: PageHeaderProps) {
  return (
    <div className="relative mb-6 overflow-hidden rounded-octo border border-octo-border/80 bg-[radial-gradient(circle_at_18%_0%,rgb(47_129_247/18%),transparent_28rem),linear-gradient(135deg,rgb(22_27_34/88%),rgb(13_17_23/76%))] p-5 shadow-[0_28px_90px_rgb(1_4_9/30%)]">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-octo-primary/60 to-transparent" />
      <div className="relative flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div className="max-w-3xl space-y-2">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-octo-primary">{eyebrow}</p>
          <h1 className="text-2xl font-semibold tracking-[-0.04em] text-octo-text-primary md:text-[34px]">{title}</h1>
          <p className="text-sm leading-6 text-octo-text-secondary">{description}</p>
        </div>
        {actions && <div className="flex shrink-0 flex-wrap gap-2">{actions}</div>}
      </div>
    </div>
  )
}
