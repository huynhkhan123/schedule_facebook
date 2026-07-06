type PanelProps = {
  title?: string
  eyebrow?: string
  children: React.ReactNode
  className?: string
}

export function Panel({ title, eyebrow, children, className = '' }: PanelProps) {
  return (
    <section className={`relative overflow-hidden rounded-octo border border-octo-border/90 bg-[linear-gradient(135deg,rgb(255_255_255/4%),transparent_36%),rgb(22_27_34/92%)] p-4 shadow-[0_24px_80px_rgb(1_4_9/28%)] backdrop-blur transition hover:border-octo-border-hover ${className}`}>
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-octo-primary/45 to-transparent" />
      {(eyebrow || title) && (
        <div className="relative mb-4 space-y-1">
          {eyebrow && <p className="text-xs font-semibold uppercase tracking-[0.16em] text-octo-neutral">{eyebrow}</p>}
          {title && <h2 className="text-base font-semibold tracking-[-0.02em] text-octo-text-primary">{title}</h2>}
        </div>
      )}
      <div className="relative">{children}</div>
    </section>
  )
}
