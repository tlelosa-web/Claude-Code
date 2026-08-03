'use client'

import { useState, useTransition } from 'react'
import { createSalesOrder, checkStockAndReadySO, cancelSalesOrder } from '@/lib/actions/sales-orders'
import type { SalesOrder, Customer, RawMaterial as Item } from '@/lib/types'
import { useRouter } from 'next/navigation'

interface Props { orders: SalesOrder[]; customers: Customer[]; finishedGoods: Item[] }
interface SOLine { item_id: string; quantity: number; unit_price: number }

const STATUS_BADGE: Record<string, string> = {
    'Confirmed': 'badge badge-confirmed', 'Ready for Dispatch': 'badge badge-dispatch',
    'Dispatched': 'badge badge-dispatched', 'Cancelled': 'badge badge-cancelled',
}

export default function SalesOrdersClient({ orders, customers, finishedGoods }: Props) {
    const router = useRouter()
    const [isPending, startTransition] = useTransition()
    const [modalOpen, setModalOpen] = useState(false)
    const [lines, setLines] = useState<SOLine[]>([])
    const [toast, setToast] = useState<{ msg: string; type: 'success' | 'error' } | null>(null)

    function showToast(msg: string, type: 'success' | 'error' = 'success') {
        setToast({ msg, type }); setTimeout(() => setToast(null), 3500)
    }
    const total = lines.reduce((s, l) => s + l.quantity * l.unit_price, 0)

    function addLine() { setLines(prev => [...prev, { item_id: '', quantity: 1, unit_price: 0 }]) }
    function removeLine(i: number) { setLines(prev => prev.filter((_, idx) => idx !== i)) }
    function updateLine(i: number, field: keyof SOLine, val: string | number) {
        setLines(prev => prev.map((l, idx) => {
            if (idx !== i) return l
            const updated = { ...l, [field]: val }
            if (field === 'item_id') {
                const item = finishedGoods.find(f => f.id === val)
                if (item) updated.unit_price = item.sales_price ?? 0
            }
            return updated
        }))
    }

    function handleCreate(e: React.FormEvent<HTMLFormElement>) {
        e.preventDefault()
        if (lines.length === 0) { showToast('Add at least one line item', 'error'); return }
        const fd = new FormData(e.currentTarget)
        fd.set('items', JSON.stringify(lines.filter(l => l.item_id)))
        startTransition(async () => {
            await createSalesOrder(fd)
            router.refresh()
            setModalOpen(false)
            setLines([])
            showToast('Sales order confirmed')
        })
    }

    function doAction(fn: () => Promise<void>, msg: string) {
        startTransition(async () => {
            try { await fn(); router.refresh(); showToast(msg) }
            catch (e: any) { showToast(e.message ?? 'Error', 'error') }
        })
    }

    return (
        <>
            {toast && (
                <div className={`fixed bottom-5 right-5 px-4 py-3 rounded-xl text-white font-medium text-sm shadow-dropdown z-[9999] animate-slide-in
          ${toast.type === 'error' ? 'bg-danger' : 'bg-success'}`}>{toast.msg}</div>
            )}

            <div className="card">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-navy">Sales Orders</h3>
                    <button onClick={() => { setLines([]); setModalOpen(true) }} className="btn btn-primary">
                        <i className="fas fa-plus" /> New SO
                    </button>
                </div>
                <div className="table-wrap">
                    <table className="data-table">
                        <thead><tr><th>Order #</th><th>Customer</th><th>Items</th><th>Status</th><th>Created</th><th>Delivery</th><th>Actions</th></tr></thead>
                        <tbody>
                            {orders.length === 0 && <tr><td colSpan={7} className="text-center text-muted py-8">No sales orders yet.</td></tr>}
                            {orders.map(so => (
                                <tr key={so.id}>
                                    <td><strong>{so.order_number}</strong></td>
                                    <td>{(so as any).customer?.name ?? 'N/A'}</td>
                                    <td>{(so.so_items ?? []).length}</td>
                                    <td><span className={STATUS_BADGE[so.status] ?? 'badge'}>{so.status}</span></td>
                                    <td>{new Date(so.created_at).toLocaleDateString()}</td>
                                    <td>{so.delivery_date ? new Date(so.delivery_date).toLocaleDateString() : '—'}</td>
                                    <td><div className="flex gap-1">
                                        {so.status === 'Confirmed' && (
                                            <button onClick={() => doAction(() => checkStockAndReadySO(so.id), `${so.order_number} ready for dispatch`)}
                                                className="btn btn-sm btn-outline" disabled={isPending}>Check Stock</button>
                                        )}
                                        {(so.status === 'Confirmed' || so.status === 'Ready for Dispatch') && (
                                            <button onClick={() => doAction(() => cancelSalesOrder(so.id), 'Order cancelled')}
                                                className="btn btn-sm btn-danger" disabled={isPending}>Cancel</button>
                                        )}
                                    </div></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {modalOpen && (
                <div className="modal-backdrop" onClick={e => e.target === e.currentTarget && setModalOpen(false)}>
                    <div className="modal-box max-w-2xl">
                        <div className="modal-header">
                            <h3 className="text-lg font-semibold text-navy">Create Sales Order</h3>
                            <button onClick={() => setModalOpen(false)} className="btn btn-ghost btn-sm"><i className="fas fa-times" /></button>
                        </div>
                        <form onSubmit={handleCreate}>
                            <div className="modal-body">
                                <div className="grid grid-cols-2 gap-4 mb-5">
                                    <div><label className="form-label">Customer *</label>
                                        <select name="customer_id" className="form-select" required>
                                            <option value="">Select customer…</option>
                                            {customers.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                                        </select></div>
                                    <div><label className="form-label">Delivery Date *</label>
                                        <input type="date" name="delivery_date" className="form-input" required /></div>
                                </div>
                                <div className="border border-gray-200 rounded-xl p-4 bg-gray-50">
                                    <div className="flex items-center justify-between mb-3">
                                        <h4 className="font-semibold text-navy text-sm">Order Items</h4>
                                        <button type="button" onClick={addLine} className="btn btn-sm btn-outline">
                                            <i className="fas fa-plus" /> Add Item
                                        </button>
                                    </div>
                                    <div className="grid grid-cols-12 text-xs font-semibold text-muted mb-2 border-b pb-1">
                                        <div className="col-span-5">Product</div><div className="col-span-3">Qty</div>
                                        <div className="col-span-3">Unit Price (R)</div><div className="col-span-1"></div>
                                    </div>
                                    {lines.map((line, i) => (
                                        <div key={i} className="grid grid-cols-12 gap-2 mb-2 items-center">
                                            <div className="col-span-5">
                                                <select className="form-select text-sm" value={line.item_id} onChange={e => updateLine(i, 'item_id', e.target.value)}>
                                                    <option value="">Product…</option>
                                                    {finishedGoods.map(f => <option key={f.id} value={f.id}>{f.code}</option>)}
                                                </select>
                                            </div>
                                            <div className="col-span-3">
                                                <input type="number" className="form-input text-sm" min="1" step="1"
                                                    value={line.quantity} onChange={e => updateLine(i, 'quantity', parseFloat(e.target.value))} />
                                            </div>
                                            <div className="col-span-3">
                                                <input type="number" className="form-input text-sm" min="0" step="0.01"
                                                    value={line.unit_price} onChange={e => updateLine(i, 'unit_price', parseFloat(e.target.value))} />
                                            </div>
                                            <div className="col-span-1">
                                                <button type="button" onClick={() => removeLine(i)} className="btn btn-sm btn-danger">
                                                    <i className="fas fa-times" />
                                                </button>
                                            </div>
                                        </div>
                                    ))}
                                    <p className="text-sm font-semibold mt-2 text-navy">Estimated SO Value: R{total.toFixed(2)}</p>
                                </div>
                            </div>
                            <div className="modal-footer">
                                <button type="button" onClick={() => setModalOpen(false)} className="btn btn-ghost">Cancel</button>
                                <button type="submit" className="btn btn-primary" disabled={isPending}>
                                    {isPending ? <i className="fas fa-spinner fa-spin" /> : null} Confirm Order
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </>
    )
}
