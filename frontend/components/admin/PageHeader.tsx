type PageHeaderProps = {
  eyebrow: string
  title: string
  description: string
  actions?: React.ReactNode
}

export function PageHeader({ eyebrow, title, description, actions }: PageHeaderProps) {
  return (
    <div className="mb-6 flex flex-col gap-4 border-b border-octo-border pb-5 md:flex-row md:items-end md:justify-between">
      <div className="max-w-3xl space-y-2">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-octo-primary">{eyebrow}</p>
        <h1 className="text-2xl font-semibold tracking-[-0.03em] text-octo-text-primary md:text-[32px]">{title}</h1>
        <p className="text-sm leading-6 text-octo-text-secondary">{description}</p>
      </div>
      {actions && <div className="flex shrink-0 flex-wrap gap-2">{actions}</div>}
    </div>
  )
}
