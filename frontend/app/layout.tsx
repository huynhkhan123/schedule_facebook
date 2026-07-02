import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Bảng điều khiển đăng nhóm',
  description: 'Dashboard quản trị local cho workflow đăng nhóm Facebook an toàn',
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="vi">
      <body>{children}</body>
    </html>
  )
}
