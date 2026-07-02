'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

const navigationItems = [
  { href: '/tong-quan', label: 'Tổng quan', code: 'OVR' },
  { href: '/nhom', label: 'Nhóm', code: 'GRP' },
  { href: '/bai-viet', label: 'Bài viết', code: 'PST' },
  { href: '/chien-dich', label: 'Chiến dịch', code: 'CMP' },
  { href: '/ket-noi', label: 'Kết nối', code: 'LNK' },
  { href: '/nhat-ky', label: 'Nhật ký', code: 'LOG' },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="hidden min-h-screen w-64 shrink-0 border-r border-octo-border bg-octo-background px-3 py-4 lg:block">
      <Link href="/tong-quan" className="mb-5 flex items-center gap-3 rounded-octo border border-octo-border bg-octo-surface px-3 py-3 hover:border-octo-border-hover">
        <span className="grid h-8 w-8 place-items-center rounded-octo bg-octo-primary/15 font-mono text-sm font-medium text-octo-primary">FG</span>
        <span>
          <span className="block text-sm font-semibold tracking-[-0.02em] text-octo-text-primary">Group Admin</span>
          <span className="block text-xs text-octo-text-secondary">Safety-first local</span>
        </span>
      </Link>

      <nav aria-label="Điều hướng quản trị" className="space-y-1">
        {navigationItems.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-octo border-l-2 px-3 py-2 text-sm font-medium ${
                isActive
                  ? 'border-octo-orange bg-octo-surface text-octo-text-primary'
                  : 'border-transparent text-octo-text-secondary hover:bg-octo-surface hover:text-octo-text-primary'
              }`}
            >
              <span className="font-mono text-[11px] text-octo-neutral">{item.code}</span>
              {item.label}
            </Link>
          )
        })}
      </nav>
    </aside>
  )
}
