'use client'

import { useState, useTransition } from 'react'
import { createProductionOrder, startProductionOrder, completeProductionOrder, cancelProductionOrder } from '@/lib/actions/production'
import type { ProductionOrder, RawMaterial as Item } from '@/lib/types'
import { useRouter } from 'next/navigation'

interface Props { 
    orders: ProductionOrder[]; 
    finishedGoods: Item[]; 
    locations: { id: string; name: string }[] 
}

const STATUS_BADGE: Record<string, string> = {
    'Pending': 'badge badge-pending', 'In Progress': 'badge badge-in-progress',
    'Completed': 'badge badge-completed', 'Cancelled': 'badge badge-cancelled',
}

export default function ProductionClient({ orders, finishedGoods, locations }: Props) {
    const router = useRouter()
    const [isPending, startTransition] = useTransition()
    const [modalOpen, setModalOpen] = useState(false)
    const [completeModalOpen, setCompleteModalOpen] = useState<string | null>(null)
    const [toast, setToast] = useState<{ msg: string; type: 'success' | 'error' } | null>(null)

    function showToast(msg: string, type: 'success' | 'error' = 'success') {
        setToast({ msg, type }); setTimeout(() => setToast(null), 3500)
    }

    function handleCreate(e: React.FormEvent<HTMLFormElement>) {
        e.preventDefault()
        const fd = new FormData(e.currentTarget)
        startTransition(async () => {
            await createProductionOrder(fd)
            router.refresh()
            setModalOpen(false)
            showToast('Production order created')
        })
    }

    function handleComplete(e: React.FormEvent<HTMLFormElement>) {
        e.preventDefault()
        if (!completeModalOpen) return
        const fd = new FormData(e.currentTarget)
        const locId = fd.get('location_id') as string
        const batchNo = fd.get('batch_number') as string
        
        startTransition(async () => {
            try {
                await completeProductionOrder(completeModalOpen, locId, batchNo)
                router.refresh()
                setCompleteModalOpen(null)
                showToast('MO completed & stock received')
            } catch (e: any) {
                showToast(e.message, 'error')
            }
        })
    }

    function doAction(fn: () => Promise<void>, msg: string, errMsg = 'Failed') {
        startTransition(async () => {
            try { await fn(); router.refresh(); showToast(msg) }
            catch (e: any) { showToast(e.message ?? errMsg, 'error') }
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
                    <h3 className="text-lg font-semibold text-navy">Manufacturing Orders</h3>
                    <button onClick={() => setModalOpen(true)} className="btn btn-primary">
                        <i className="fas fa-plus" /> New MO
                    </button>
                </div>
                <div className="table-wrap">
                    <table className="data-table">
                        <thead><tr><th>Order #</th><th>Item</th><th>Qty</th><th>Status</th><th>Created</th><th>Due Date</th><th>Actions</th></tr></thead>
                        <tbody>
                            {orders.length === 0 && <tr><td colSpan={7} className="text-center text-muted py-8">No manufacturing orders yet.</td></tr>}
                            {orders.map(o => (
                                <tr key={o.id}>
                                    <td><strong>{o.order_number}</strong></td>
                                    <td>{(o as any).item?.code ?? 'N/A'}</td>
                                    <td>{o.quantity}</td>
                                    <td>
                                        <div className="flex flex-col gap-1">
                                            <span className={STATUS_BADGE[o.status] ?? 'badge'}>{o.status}</span>
                                            {o.status === 'In Progress' && (o as any).production_tasks && (
                                                <div className="text-[10px] text-muted space-y-0.5">
                                                    {(o as any).production_tasks.map((t: any) => (
                                                        <div key={t.id} className="flex items-center gap-1">
                                                            <i className={`fas ${t.status === 'Completed' ? 'fa-check-circle text-success' : 'fa-circle text-gray-300'}`} />
                                                            <span>{t.operation_name}</span>
                                                        </div>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    </td>
                                    <td>{new Date(o.created_at).toLocaleDateString()}</td>
                                    <td>{o.due_date ? new Date(o.due_date).toLocaleDateString() : '—'}</td>
                                    <td>
                                        <div className="flex gap-1 flex-wrap">
                                            {o.status === 'Pending' && (
                                                <button onClick={() => doAction(() => startProductionOrder(o.id), 'Manufacturing started (tasks generated)')}
                                                    className="btn btn-sm btn-outline" disabled={isPending}>Start</button>
                                            )}
                                            {o.status === 'In Progress' && (
                                                <button onClick={() => setCompleteModalOpen(o.id)}
                                                    className="btn btn-sm btn-success" disabled={isPending}>Complete</button>
                                            )}
                                            {(o.status === 'Pending' || o.status === 'In Progress') && (
                                                <button onClick={() => doAction(() => cancelProductionOrder(o.id), 'Order cancelled')}
                                                    className="btn btn-sm btn-danger" disabled={isPending}>Cancel</button>
                                            )}
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {modalOpen && (
                <div className="modal-backdrop" onClick={e => e.target === e.currentTarget && setModalOpen(false)}>
                    <div className="modal-box max-w-md">
                        <div className="modal-header">
                            <h3 className="text-lg font-semibold text-navy">Create Manufacturing Order</h3>
                            <button onClick={() => setModalOpen(false)} className="btn btn-ghost btn-sm"><i className="fas fa-times" /></button>
                        </div>
                        <form onSubmit={handleCreate}>
                            <div className="modal-body space-y-4">
                                <div><label className="form-label">Item to Manufacture *</label>
                                    <select name="item_id" className="form-select" required>
                                        <option value="">Select item…</option>
                                        {finishedGoods.map(f => <option key={f.id} value={f.id}>{f.code} — {f.description}</option>)}
                                    </select></div>
                                <div><label className="form-label">Quantity *</label>
                                    <input type="number" name="quantity" className="form-input" min="1" step="1" defaultValue={1} required /></div>
                                <div><label className="form-label">Required By Date *</label>
                                    <input type="date" name="due_date" className="form-input" required /></div>
                            </div>
                            <div className="modal-footer">
                                <button type="button" onClick={() => setModalOpen(false)} className="btn btn-ghost">Cancel</button>
                                <button type="submit" className="btn btn-primary" disabled={isPending}>
                                    {isPending ? <i className="fas fa-spinner fa-spin" /> : null} Create Order
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {completeModalOpen && (
                <div className="modal-backdrop" onClick={() => setCompleteModalOpen(null)}>
                    <div className="modal-box max-w-sm" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3 className="text-lg font-semibold text-navy">Receive Finished Product</h3>
                            <button onClick={() => setCompleteModalOpen(null)} className="btn btn-ghost btn-sm"><i className="fas fa-times" /></button>
                        </div>
                        <form onSubmit={handleComplete}>
                            <div className="modal-body space-y-4">
                                <div><label className="form-label">Receiving Location *</label>
                                    <select name="location_id" className="form-select" required>
                                        <option value="">Select location…</option>
                                        {locations.map(l => <option key={l.id} value={l.id}>{l.name}</option>)}
                                    </select></div>
                                <div><label className="form-label">Batch Number *</label>
                                    <input type="text" name="batch_number" className="form-input" placeholder="e.g. B-001" required /></div>
                            </div>
                            <div className="modal-footer">
                                <button type="button" onClick={() => setCompleteModalOpen(null)} className="btn btn-ghost">Cancel</button>
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
