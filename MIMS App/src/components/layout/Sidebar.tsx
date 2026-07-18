'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'

const navItems = [
    { href: '/', label: 'Home', icon: 'fa-home' },
    { href: '/inventory', label: 'Inventory', icon: 'fa-cubes' },
    { href: '/inventory/reorder', label: 'Reorder', icon: 'fa-exclamation-circle' },
    { href: '/products', label: 'Products', icon: 'fa-box-open' },
    { href: '/production', label: 'Production', icon: 'fa-tasks' },
    { href: '/production/tasks', label: 'Tasks', icon: 'fa-clipboard-check' },
    { href: '/suppliers', label: 'Suppliers', icon: 'fa-truck' },
    { href: '/purchase-orders', label: 'Purchase Orders', icon: 'fa-shopping-cart' },
    { href: '/customers', label: 'Customers', icon: 'fa-users' },
    { href: '/sales-orders', label: 'Sales Orders', icon: 'fa-hand-holding-usd' },
    { href: '/dispatch', label: 'Dispatch', icon: 'fa-shipping-fast' },
    { href: '/data-management', label: 'Data Mgmt', icon: 'fa-database' },
]

export default function Sidebar() {
    const pathname = usePathname()
    const router = useRouter()
    const supabase = createClient()

    async function signOut() {
        await supabase.auth.signOut()
        router.push('/login')
    }

    return (
        <aside className="sidebar">
            {/* Logo */}
            <div className="flex items-center gap-3 px-5 py-6 border-b border-white/10 shrink-0">
                <i className="fas fa-industry text-2xl text-emerald-400" />
                <div>
                    <h1 className="text-white font-bold text-lg leading-tight">MIMS ERP</h1>
                    <span className="text-xs text-white/50">v2.0 — Powered by Supabase</span>
                </div>
            </div>

            {/* Nav */}
            <nav className="flex-1 px-3 py-4 space-y-1">
                {navItems.map(item => {
                    const isActive = pathname === item.href
                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={`flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-150
                ${isActive
                                    ? 'bg-white/15 text-white shadow-sm'
                                    : 'text-white/70 hover:bg-white/10 hover:text-white'}`}
                        >
                            <i className={`fas ${item.icon} w-5 text-center text-base`} />
                            <span>{item.label}</span>
                        </Link>
                    )
                })}
            </nav>

            {/* Sign out */}
            <div className="px-3 pb-5 shrink-0">
                <button
                    onClick={signOut}
                    className="w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium
                     text-white/60 hover:bg-white/10 hover:text-white transition-all duration-150"
                >
                    <i className="fas fa-sign-out-alt w-5 text-center" />
                    <span>Sign Out</span>
                </button>
            </div>
        </aside>
    )
}
