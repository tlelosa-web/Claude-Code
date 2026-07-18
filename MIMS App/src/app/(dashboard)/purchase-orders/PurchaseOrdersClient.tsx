'use client'

import { useState, useTransition } from 'react'
import { createPurchaseOrder, receivePurchaseOrder, cancelPurchaseOrder } from '@/lib/actions/purchase-orders'
import type { PurchaseOrder, Supplier, RawMaterial as Item } from '@/lib/types'
import { useRouter } from 'next/navigation'

interface Props { 
    orders: PurchaseOrder[]; 
    suppliers: Supplier[]; 
    rawMaterials: Item[];
    locations: { id: string; name: string }[]
}
interface POLine { item_id: string; quantity: number; unit_cost: number }

const STATUS_BADGE: Record<string, string> = {
    'Ordered': 'badge badge-ordered', 'Received': 'badge badge-received', 'Cancelled': 'badge badge-cancelled',
}

export default function PurchaseOrdersClient({ orders, suppliers, rawMaterials, locations }: Props) {
    const router = useRouter()
    const [isPending, startTransition] = useTransition()
    const [modalOpen, setModalOpen] = useState(false)
    const [receiveModalOpen, setReceiveModalOpen] = useState<string | null>(null)
    const [lines, setLines] = useState<POLine[]>([])
    const [toast, setToast] = useState<{ msg: string; type: 'success' | 'error' } | null>(null)

    function showToast(msg: string, type: 'success' | 'error' = 'success') {
        setToast({ msg, type }); setTimeout(() => setToast(null), 3500)
    }

    const total = lines.reduce((s, l) => s + l.quantity * l.unit_cost, 0)

    function addLine() { setLines(prev => [...prev, { item_id: '', quantity: 1, unit_cost: 0 }]) }
    function removeLine(i: number) { setLines(prev => prev.filter((_, idx) => idx !== i)) }
    function updateLine(i: number, field: keyof POLine, val: string | number) {
        setLines(prev => prev.map((l, idx) => {
            if (idx !== i) return l
            const updated = { ...l, [field]: val }
            // Auto-fill cost from Item
            if (field === 'item_id') {
                const item = rawMaterials.find(r => r.id === val)
                if (item) updated.unit_cost = item.avg_cost
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
            await createPurchaseOrder(fd)
            router.refresh()
            setModalOpen(false)
            setLines([])
            showToast('Purchase order issued')
        })
    }

    function handleReceive(e: React.FormEvent<HTMLFormElement>) {
        e.preventDefault()
        if (!receiveModalOpen) return
        const fd = new FormData(e.currentTarget)
        const locId = fd.get('location_id') as string
        
        startTransition(async () => {
            try {
                await receivePurchaseOrder(receiveModalOpen, locId)
                router.refresh()
                setReceiveModalOpen(null)
                showToast('PO received and stock updated')
            } catch (e: any) {
                showToast(e.message, 'error')
            }
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
                    <h3 className="text-lg font-semibold text-navy">Purchase Orders</h3>
                    <button onClick={() => { setLines([]); setModalOpen(true) }} className="btn btn-primary">
                        <i className="fas fa-plus" /> New PO
                    </button>
                </div>
                <div className="table-wrap">
                    <table className="data-table">
                        <thead><tr><th>Order #</th><th>Supplier</th><th>Items</th><th>Status</th><th>Created</th><th>Delivery</th><th>Total</th><th>Actions</th></tr></thead>
                        <tbody>
                            {orders.length === 0 && <tr><td colSpan={8} className="text-center text-muted py-8">No purchase orders yet.</td></tr>}
                            {orders.map(po => (
                                <tr key={po.id}>
                                    <td><strong>{po.order_number}</strong></td>
                                    <td>{(po as any).supplier?.name ?? 'N/A'}</td>
                                    <td>{(po.po_items ?? []).length}</td>
                                    <td><span className={STATUS_BADGE[po.status] ?? 'badge'}>{po.status}</span></td>
                                    <td>{new Date(po.created_at).toLocaleDateString()}</td>
                                    <td>{po.delivery_date ? new Date(po.delivery_date).toLocaleDateString() : '—'}</td>
                                    <td>R{Number(po.total).toFixed(2)}</td>
                                    <td><div className="flex gap-1">
                                        {po.status === 'Ordered' && (
                                            <button onClick={() => setReceiveModalOpen(po.id)}
                                                className="btn btn-sm btn-success" disabled={isPending}>Receive</button>
                                        )}
                                        {po.status === 'Ordered' && (
                                            <button onClick={() => doAction(() => cancelPurchaseOrder(po.id), 'PO cancelled')}
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
                            <h3 className="text-lg font-semibold text-navy">Create Purchase Order</h3>
                            <button onClick={() => setModalOpen(false)} className="btn btn-ghost btn-sm"><i className="fas fa-times" /></button>
                        </div>
                        <form onSubmit={handleCreate}>
                            <div className="modal-body">
                                <div className="grid grid-cols-2 gap-4 mb-5">
                                    <div><label className="form-label">Supplier *</label>
                                        <select name="supplier_id" className="form-select" required>
                                            <option value="">Select supplier…</option>
                                            {suppliers.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
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
                                        <div className="col-span-5">Item</div><div className="col-span-3">Qty</div>
                                        <div className="col-span-3">Unit Cost (R)</div><div className="col-span-1"></div>
                                    </div>
                                    {lines.map((line, i) => (
                                        <div key={i} className="grid grid-cols-12 gap-2 mb-2 items-center">
                                            <div className="col-span-5">
                                                <select className="form-select text-sm" value={line.item_id} onChange={e => updateLine(i, 'item_id', e.target.value)}>
                                                    <option value="">Item…</option>
                                                    {rawMaterials.map(r => <option key={r.id} value={r.id}>{r.code}</option>)}
                                                </select>
                                            </div>
                                            <div className="col-span-3">
                                                <input type="number" className="form-input text-sm" min="1" step="1"
                                                    value={line.quantity} onChange={e => updateLine(i, 'quantity', parseFloat(e.target.value))} />
                                            </div>
                                            <div className="col-span-3">
                                                <input type="number" className="form-input text-sm" min="0" step="0.01"
                                                    value={line.unit_cost} onChange={e => updateLine(i, 'unit_cost', parseFloat(e.target.value))} />
                                            </div>
                                            <div className="col-span-1">
                                                <button type="button" onClick={() => removeLine(i)} className="btn btn-sm btn-danger">
                                                    <i className="fas fa-times" />
                                                </button>
                                            </div>
                                        </div>
                                    ))}
                                    <p className="text-sm font-semibold mt-2 text-navy">Total PO Value: R{total.toFixed(2)}</p>
                                </div>
                            </div>
                            <div className="modal-footer">
                                <button type="button" onClick={() => setModalOpen(false)} className="btn btn-ghost">Cancel</button>
                                <button type="submit" className="btn btn-primary" disabled={isPending}>
                                    {isPending ? <i className="fas fa-spinner fa-spin" /> : null} Issue PO
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {receiveModalOpen && (
                <div className="modal-backdrop" onClick={() => setReceiveModalOpen(null)}>
                    <div className="modal-box max-w-sm" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3 className="text-lg font-semibold text-navy">Receive Items</h3>
                            <button onClick={() => setReceiveModalOpen(null)} className="btn btn-ghost btn-sm"><i className="fas fa-times" /></button>
                        </div>
                        <form onSubmit={handleReceive}>
                            <div className="modal-body space-y-4">
                                <div><label className="form-label">Receiving Location *</label>
                                    <select name="location_id" className="form-select" required>
                                        <option value="">Select location…</option>
                                        {locations.map(l => <option key={l.id} value={l.id}>{l.name}</option>)}
                                    </select></div>
                                <p className="text-[10px] text-muted italic">Note: A unique batch will be automatically created using the PO number.</p>
                            </div>
                            <div className="modal-footer">
                                <button type="button" onClick={() => setReceiveModalOpen(null)} className="btn btn-ghost">Cancel</button>
                                <button type="submit" className="btn btn-success" disabled={isPending}>
                                    {isPending ? <i className="fas fa-spinner fa-spin" /> : null} Receive Stock
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </>
    )
}
