import Link from 'next/link'

type PaginationProps = {
  basePath: string
  currentPage: number
  totalPages: number
  pageSize: number
  totalItems: number
}

function pageHref(basePath: string, page: number, pageSize: number): string {
  const params = new URLSearchParams()
  params.set('page', String(page))
  params.set('limit', String(pageSize))
  return `${basePath}?${params.toString()}`
}

function getPageItems(currentPage: number, totalPages: number): Array<number | 'ellipsis'> {
  if (totalPages <= 7) {
    return Array.from({ length: totalPages }, (_, index) => index + 1)
  }

  const pages = new Set([1, totalPages, currentPage - 1, currentPage, currentPage + 1])
  const sortedPages = [...pages].filter((page) => page >= 1 && page <= totalPages).sort((a, b) => a - b)
  const items: Array<number | 'ellipsis'> = []

  for (const page of sortedPages) {
    const previous = items.at(-1)
    if (typeof previous === 'number' && page - previous > 1) {
      items.push('ellipsis')
    }
    items.push(page)
  }

  return items
}

export function Pagination({ basePath, currentPage, totalPages, pageSize, totalItems }: PaginationProps) {
  if (totalItems === 0 || totalPages <= 1) {
    return null
  }

  const startItem = (currentPage - 1) * pageSize + 1
  const endItem = Math.min(currentPage * pageSize, totalItems)
  const pageItems = getPageItems(currentPage, totalPages)
  const canGoPrevious = currentPage > 1
  const canGoNext = currentPage < totalPages

  return (
    <nav aria-label="Phân trang nhóm" className="flex flex-col gap-3 border-t border-octo-border/70 px-4 py-4 md:flex-row md:items-center md:justify-between">
      <p className="font-mono text-xs text-octo-text-secondary">
        Hiển thị <span className="text-octo-text-primary">{startItem}–{endItem}</span> / {totalItems} nhóm
      </p>
      <div className="flex flex-wrap items-center gap-2">
        <PaginationLink disabled={!canGoPrevious} href={pageHref(basePath, currentPage - 1, pageSize)} label="Trước" />
        {pageItems.map((item, index) =>
          item === 'ellipsis' ? (
            <span key={`ellipsis-${index}`} className="px-2 font-mono text-xs text-octo-neutral">
              …
            </span>
          ) : (
            <Link
              key={item}
              href={pageHref(basePath, item, pageSize)}
              aria-current={item === currentPage ? 'page' : undefined}
              className={`grid h-8 min-w-8 place-items-center rounded-octo border px-2 font-mono text-xs font-semibold ${
                item === currentPage
                  ? 'border-octo-primary/60 bg-octo-primary/15 text-octo-primary shadow-[0_0_22px_rgb(47_129_247/18%)]'
                  : 'border-octo-border bg-octo-background/60 text-octo-text-secondary hover:border-octo-border-hover hover:bg-octo-elevated hover:text-octo-text-primary'
              }`}
            >
              {item}
            </Link>
          ),
        )}
        <PaginationLink disabled={!canGoNext} href={pageHref(basePath, currentPage + 1, pageSize)} label="Sau" />
      </div>
    </nav>
  )
}

function PaginationLink({ disabled, href, label }: { disabled: boolean; href: string; label: string }) {
  if (disabled) {
    return (
      <span className="inline-flex h-8 items-center rounded-octo border border-octo-border/60 px-3 text-xs font-semibold text-octo-neutral opacity-50">
        {label}
      </span>
    )
  }

  return (
    <Link href={href} className="inline-flex h-8 items-center rounded-octo border border-octo-border bg-octo-background/60 px-3 text-xs font-semibold text-octo-text-secondary hover:border-octo-border-hover hover:bg-octo-elevated hover:text-octo-text-primary">
      {label}
    </Link>
  )
}
