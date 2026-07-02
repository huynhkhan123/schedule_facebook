type EmptyStateProps = {
  title: string
  description: string
}

export function EmptyState({ title, description }: EmptyStateProps) {
  return (
    <div className="rounded-octo border border-dashed border-octo-border bg-octo-background px-4 py-8 text-center">
      <p className="text-sm font-semibold text-octo-text-primary">{title}</p>
      <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-octo-text-secondary">{description}</p>
    </div>
  )
}
