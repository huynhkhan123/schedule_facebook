type StatCardProps = {
  label: string
  value: string | number
  description: string
  tone?: 'blue' | 'green' | 'yellow' | 'red'
}

const tones = {
  blue: 'text-octo-primary',
  green: 'text-octo-success',
  yellow: 'text-octo-warning',
  red: 'text-octo-error',
}

export function StatCard({ label, value, description, tone = 'blue' }: StatCardProps) {
  return (
    <article className="rounded-octo border border-octo-border bg-octo-surface p-4 hover:border-octo-border-hover">
      <p className="text-xs font-medium uppercase tracking-[0.12em] text-octo-neutral">{label}</p>
      <strong className={`mt-3 block font-mono text-3xl font-medium tracking-[-0.04em] ${tones[tone]}`}>{value}</strong>
      <p className="mt-2 text-sm text-octo-text-secondary">{description}</p>
    </article>
  )
}
