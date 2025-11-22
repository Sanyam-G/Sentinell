import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'CloudOps Store - Enterprise Solutions',
  description: 'Premium enterprise cloud operations tools',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
