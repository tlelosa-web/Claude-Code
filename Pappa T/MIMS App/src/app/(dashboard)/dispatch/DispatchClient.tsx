'use client'

import { useTransition, useState } from 'react'
import { dispatchSalesOrder } from '@/lib/actions/sales-orders'
import type { SalesOrder } from '@/lib/types'
import { useRouter } from 'next/navigation'

interface Props { 
    orders: SalesOrder[]; 
    locations: { id: string; name: string }[];
    batches: any[]
}

export default function DispatchClient({ orders, locations, batches }: Props) {
    const router = useRouter()
    const [isPending, startTransition] = useTransition()
    const [dispatchModalOpen, setDispatchModalOpen] = useState<SalesOrder | null>(null)
    const [toast, setToast] = useState<{ msg: string; type: 'success' | 'error' } | null>(null)

    function showToast(msg: string, type: 'success' | 'error' = 'success') {
        setToast({ msg, type }); setTimeout(() => setToast(null), 3500)
    }

    function handleDispatch(e: React.FormEvent<HTMLFormElement>) {
        e.preventDefault()
        if (!dispatchModalOpen) return
        const fd = new FormData(e.currentTarget)
        const locId = fd.get('location_id') as string
        const batchNo = fd.get('batch_number') as string
        
        startTransition(async () => {
            try {
                await dispatchSalesOrder(dispatchModalOpen.id, locId, batchNo)
                router.refresh()
                setDispatchModalOpen(null)
                showToast(`${dispatchModalOpen.order_number} dispatched successfully`)
            } catch (e: any) {
                showToast(e.message ?? 'Dispatch failed', 'error')
            }
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
                    <h3 className="text-lg font-semibold text-navy">Ready for Dispatch</h3>
                    <span className="badge badge-dispatch">{orders.length} orders</span>
                </div>

                {orders.length === 0 ? (
                    <div className="text-center py-16 text-muted">
                        <i className="fas fa-shipping-fast text-4xl mb-3 text-gray-300" />
                        <p className="font-medium">No orders ready for dispatch.</p>
                        <p className="text-sm mt-1">Go to Sales Orders and check stock to move an order here.</p>
                    </div>
                ) : (
                    <div className="table-wrap">
                        <table className="data-table">
                            <thead><tr><th>SO #</th><th>Customer</th><th>Items</th><th>Total Qty</th><th>Status</th><th>Action</th></tr></thead>
                            <tbody>
                                {orders.map(so => {
                                    const totalQty = (so.so_items ?? []).reduce((s: number, i: any) => s + i.quantity, 0)
                                    return (
                                        <tr key={so.id}>
                                            <td><strong>{so.order_number}</strong></td>
                                            <td>{(so as any).customer?.name ?? 'N/A'}</td>
                                            <td>{(so.so_items ?? []).length}</td>
                                            <td>{totalQty}</td>
                                            <td><span className="badge badge-dispatch">Ready</span></td>
                                            <td>
                                                <button
                                                    onClick={() => setDispatchModalOpen(so)}
                                                    disabled={isPending}
                                                    className="btn btn-success btn-sm"
                                                >
                                                    <i className="fas fa-shipping-fast" /> Dispatch
                                                </button>
                                            </td>
                                        </tr>
                                    )
                                })}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {dispatchModalOpen && (
                <div className="modal-backdrop" onClick={() => setDispatchModalOpen(null)}>
                    <div className="modal-box max-w-sm" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3 className="text-lg font-semibold text-navy">Dispatch Order</h3>
                            <button onClick={() => setDispatchModalOpen(null)} className="btn btn-ghost btn-sm"><i className="fas fa-times" /></button>
                        </div>
                        <form onSubmit={handleDispatch}>
                            <div className="modal-body space-y-4">
                                <p className="text-sm text-muted">Select the source for fulfillment:</p>
                                <div><label className="form-label">Warehouse Location *</label>
                                    <select name="location_id" className="form-select" required>
                                        <option value="">Select location…</option>
                                        {locations.map(l => <option key={l.id} value={l.id}>{l.name}</option>)}
                                    </select></div>
                                <div><label className="form-label">Source Batch *</label>
                                    <select name="batch_number" className="form-select" required>
                                        <option value="">Select batch…</option>
                                        {/* Ideally filter batches by items in the SO, but for now we list all for simplicity */}
                                        {batches.map(b => (
                                            <option key={b.id} value={b.batch_number}>
                                                {b.batch_number} ({b.item?.code}) — At {b.location?.name}
                                            </option>
                                        ))}
                                    </select></div>
                            </div>
                            <div className="modal-footer">
                                <button type="button" onClick={() => setDispatchModalOpen(null)} className="btn btn-ghost">Cancel</button>
                                <button type="submit" className="btn btn-success" disabled={isPending}>
                                    {isPending ? <i className="fas fa-spinner fa-spin" /> : null} Ship Order
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </>
    )
}
