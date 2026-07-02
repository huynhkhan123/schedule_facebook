type AdminTableProps = {
  headers: string[]
  children: React.ReactNode
}

export function AdminTable({ headers, children }: AdminTableProps) {
  return (
    <div className="overflow-hidden rounded-octo border border-octo-border">
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-left text-sm">
          <thead className="bg-octo-elevated text-xs uppercase tracking-[0.12em] text-octo-neutral">
            <tr>
              {headers.map((header) => (
                <th key={header} className="border-b border-octo-border px-4 py-3 font-semibold">
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-octo-border bg-octo-surface">{children}</tbody>
        </table>
      </div>
    </div>
  )
}
