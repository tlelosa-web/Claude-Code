import { createClient } from '@/lib/supabase/server'
import TopBar from '@/components/layout/TopBar'
import { calcRisk } from '@/lib/types'
import { getItems } from '@/lib/actions/items'

export default async function HomePage() {
    const supabase = await createClient()
    const [items, { data: pos }, { data: wos }] = await Promise.all([
        getItems(),
        supabase.from('purchase_orders').select('status'),
        supabase.from('production_orders').select('status'),
    ])

    const inventoryValue = items.reduce((s, r) => s + (r.stock ?? 0) * (r.avg_cost ?? 0), 0)
    const pendingProd = (wos ?? []).filter((w: any) => w.status === 'Pending' || w.status === 'In Progress').length
    const poIssued = (pos ?? []).filter((p: any) => p.status === 'Ordered').length
    const lowStock = items.filter((i: any) =>
        calcRisk({ stock: i.stock, demand: i.demand, min_stock: i.min_stock, on_order: i.on_order ?? 0 }) === 'High Risk'
    ).length

    const modules = [
        { href: '/inventory', label: 'Inventory', icon: 'fa-cubes', color: 'bg-blue-100 text-blue-600' },
        { href: '/products', label: 'Products', icon: 'fa-box-open', color: 'bg-purple-100 text-purple-600' },
        { href: '/production', label: 'Production', icon: 'fa-tasks', color: 'bg-red-100 text-red-600' },
        { href: '/suppliers', label: 'Suppliers', icon: 'fa-truck', color: 'bg-yellow-100 text-yellow-600' },
        { href: '/purchase-orders', label: 'Purchase Orders', icon: 'fa-shopping-cart', color: 'bg-green-100 text-green-600' },
        { href: '/customers', label: 'Customers', icon: 'fa-users', color: 'bg-indigo-100 text-indigo-600' },
        { href: '/sales-orders', label: 'Sales Orders', icon: 'fa-hand-holding-usd', color: 'bg-cyan-100 text-cyan-600' },
        { href: '/dispatch', label: 'Dispatch', icon: 'fa-shipping-fast', color: 'bg-orange-100 text-orange-600' },
    ]

    return (
        <>
            <TopBar pageTitle="Home" />

            {/* KPI Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
                <a href="/inventory" className="stat-card group">
                    <div className="stat-icon bg-blue-100 text-blue-600 group-hover:scale-110 transition-transform">
                        <i className="fas fa-warehouse" />
                    </div>
                    <div>
                        <p className="text-2xl font-bold text-navy">
                            R{inventoryValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </p>
                        <p className="text-muted text-sm">Inventory Value</p>
                    </div>
                </a>
                <a href="/production" className="stat-card group">
                    <div className="stat-icon bg-red-100 text-red-500 group-hover:scale-110 transition-transform">
                        <i className="fas fa-exclamation-triangle" />
                    </div>
                    <div>
                        <p className="text-2xl font-bold text-navy">{pendingProd}</p>
                        <p className="text-muted text-sm">Active Production</p>
                    </div>
                </a>
                <a href="/purchase-orders" className="stat-card group">
                    <div className="stat-icon bg-green-100 text-green-600 group-hover:scale-110 transition-transform">
                        <i className="fas fa-file-invoice" />
                    </div>
                    <div>
                        <p className="text-2xl font-bold text-navy">{poIssued}</p>
                        <p className="text-muted text-sm">POs Issued</p>
                    </div>
                </a>
                <a href="/inventory" className="stat-card group">
                    <div className="stat-icon bg-yellow-100 text-yellow-600 group-hover:scale-110 transition-transform">
                        <i className="fas fa-bell" />
                    </div>
                    <div>
                        <p className="text-2xl font-bold text-navy">{lowStock}</p>
                        <p className="text-muted text-sm">Low Stock Alerts</p>
                    </div>
                </a>
            </div>

            {/* Module Grid */}
            <div className="card mb-6">
                <h3 className="text-lg font-semibold text-navy mb-4">Core Modules</h3>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                    {modules.map(m => (
                        <a key={m.href} href={m.href}
                            className="flex flex-col items-center gap-2 p-4 border border-gray-100 rounded-xl
                          hover:shadow-card hover:border-primary/30 transition-all duration-200 group">
                            <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-xl ${m.color} group-hover:scale-110 transition-transform`}>
                                <i className={`fas ${m.icon}`} />
                            </div>
                            <span className="text-sm font-semibold text-navy text-center">{m.label}</span>
                        </a>
                    ))}
                </div>
            </div>

            {/* System Status */}
            <div className="card">
                <h3 className="text-lg font-semibold text-navy mb-2">System Status</h3>
                <p className="text-muted text-sm">
                    Welcome to <strong>MIMS ERP v2 (MRP Stage 2)</strong>. Data is live from Supabase. Use{' '}
                    <a href="/data-management" className="text-primary underline">Data Management</a> to seed the latest demo data.
                </p>
            </div>
        </>
    )
}
