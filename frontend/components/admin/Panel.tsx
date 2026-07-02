type PanelProps = {
  title?: string
  eyebrow?: string
  children: React.ReactNode
  className?: string
}

export function Panel({ title, eyebrow, children, className = '' }: PanelProps) {
  return (
    <section className={`rounded-octo border border-octo-border bg-octo-surface p-4 ${className}`}>
      {(eyebrow || title) && (
        <div className="mb-4 space-y-1">
          {eyebrow && <p className="text-xs font-semibold uppercase tracking-[0.16em] text-octo-neutral">{eyebrow}</p>}
          {title && <h2 className="text-base font-semibold tracking-[-0.02em] text-octo-text-primary">{title}</h2>}
        </div>
      )}
      {children}
    </section>
  )
}
