import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
    title: 'MIMS ERP v2 — Manufacturing & Inventory',
    description: 'Full-stack MRP system for manufacturing and inventory management',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
    return (
        <html lang="en">
            <body>{children}</body>
        </html>
    )
}
