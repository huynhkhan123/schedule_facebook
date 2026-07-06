type AdminTableProps = {
  headers: string[]
  children: React.ReactNode
}

export function AdminTable({ headers, children }: AdminTableProps) {
  return (
    <div className="overflow-hidden rounded-octo border border-octo-border/90 bg-octo-background/42 shadow-[0_22px_70px_rgb(1_4_9/28%)]">
      <div className="max-h-[680px] overflow-auto">
        <table className="w-full border-collapse text-left text-sm">
          <thead className="sticky top-0 z-10 bg-octo-elevated/95 text-xs uppercase tracking-[0.12em] text-octo-neutral shadow-[0_1px_0_rgb(48_54_61)] backdrop-blur">
            <tr>
              {headers.map((header) => (
                <th key={header} className="border-b border-octo-border px-4 py-3 font-semibold">
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-octo-border/70 bg-octo-surface/82">{children}</tbody>
        </table>
      </div>
    </div>
  )
}
