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
    <aside className="hidden w-64 shrink-0 border-r border-octo-border/80 bg-octo-background/82 px-3 py-4 shadow-[18px_0_70px_rgb(1_4_9/34%)] backdrop-blur-xl lg:sticky lg:top-0 lg:block lg:h-screen lg:overflow-y-auto">
      <Link href="/tong-quan" className="group mb-5 flex items-center gap-3 rounded-octo border border-octo-border/90 bg-[linear-gradient(135deg,rgb(22_27_34/96%),rgb(28_33_40/72%))] px-3 py-3 shadow-[0_18px_48px_rgb(1_4_9/24%)] hover:border-octo-primary/50">
        <span className="grid h-9 w-9 place-items-center rounded-octo bg-octo-primary/15 font-mono text-sm font-semibold text-octo-primary shadow-[0_0_28px_rgb(47_129_247/18%)] group-hover:bg-octo-primary/20">FG</span>
        <span>
          <span className="block text-sm font-semibold tracking-[-0.02em] text-octo-text-primary">Group Admin</span>
          <span className="block text-xs text-octo-text-secondary">Local bridge</span>
        </span>
      </Link>

      <nav aria-label="Điều hướng quản trị" className="space-y-1.5">
        {navigationItems.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`group relative flex items-center gap-3 overflow-hidden rounded-octo border px-3 py-2.5 text-sm font-medium transition-transform hover:-translate-y-0.5 ${
                isActive
                  ? 'border-octo-primary/40 bg-octo-primary/12 text-octo-text-primary shadow-[0_0_34px_rgb(47_129_247/12%)]'
                  : 'border-transparent text-octo-text-secondary hover:border-octo-border-hover hover:bg-octo-surface/90 hover:text-octo-text-primary'
              }`}
            >
              <span className={`absolute inset-y-2 left-0 w-0.5 rounded-full ${isActive ? 'bg-octo-orange shadow-[0_0_18px_rgb(247_129_102/55%)]' : 'bg-transparent'}`} />
              <span className={`font-mono text-[11px] ${isActive ? 'text-octo-primary' : 'text-octo-neutral group-hover:text-octo-primary'}`}>{item.code}</span>
              {item.label}
            </Link>
          )
        })}
      </nav>
    </aside>
  )
}
