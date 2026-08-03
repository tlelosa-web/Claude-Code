'use client'

import { useState, useTransition } from 'react'
import { upsertItem, deleteItem } from '@/lib/actions/items'
import { calcRisk, type RawMaterial as Item, type Supplier } from '@/lib/types'
import { useRouter } from 'next/navigation'

interface Props { 
    rawMaterials: Item[]; 
    suppliers: Supplier[];
    batches: any[];
    locations: { id: string; name: string }[]
}

const RISK_BADGE: Record<string, string> = {
    'R1': 'badge badge-r1',
    'Medium Risk': 'badge badge-medium',
    'High Risk': 'badge badge-high',
}

export default function InventoryClient({ rawMaterials, suppliers, batches, locations }: Props) {
    const router = useRouter()
    const [isPending, startTransition] = useTransition()
    const [search, setSearch] = useState('')
    const [modalOpen, setModalOpen] = useState(false)
    const [viewBatches, setViewBatches] = useState<string | null>(null)
    const [editItem, setEditItem] = useState<Item | null>(null)
    const [toast, setToast] = useState<{ msg: string; type: 'success' | 'error' } | null>(null)

    const filtered = rawMaterials.filter(r =>
        `${r.code} ${r.description} ${r.category}`.toLowerCase().includes(search.toLowerCase())
    )

    function showToast(msg: string, type: 'success' | 'error' = 'success') {
        setToast({ msg, type }); setTimeout(() => setToast(null), 3000)
    }

    function openAdd() { setEditItem(null); setModalOpen(true) }
    function openEdit(r: Item) { setEditItem(r); setModalOpen(true) }
    function close() { setModalOpen(false) }

    function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
        e.preventDefault()
        const fd = new FormData(e.currentTarget)
        fd.set('type', 'Material')
        startTransition(async () => {
            await upsertItem(fd)
            router.refresh()
            close()
            showToast(editItem ? 'Material updated' : 'Material added')
        })
    }

    function handleDelete(id: string) {
        if (!confirm('Delete this material?')) return
        startTransition(async () => {
            await deleteItem(id)
            router.refresh()
            showToast('Material deleted')
        })
    }

    const itemBatches = batches.filter(b => b.item_id === viewBatches)

    return (
        <>
            {toast && (
                <div className={`fixed bottom-5 right-5 px-4 py-3 rounded-xl text-white font-medium text-sm shadow-dropdown z-[9999] animate-slide-in
          ${toast.type === 'success' ? 'bg-success' : 'bg-danger'}`}>{toast.msg}</div>
            )}

            <div className="card">
                <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
                    <div className="flex items-center gap-3">
                        <h3 className="text-lg font-semibold text-navy">Materials Inventory</h3>
                        <input type="text" placeholder="Search…" value={search} onChange={e => setSearch(e.target.value)}
                            className="form-input w-52 text-sm py-1.5" />
                    </div>
                    <button onClick={openAdd} className="btn btn-primary"><i className="fas fa-plus" /> Add Material</button>
                </div>

                <div className="table-wrap">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Code</th><th>Description</th><th>Supplier</th>
                                <th>On Hand</th><th>Committed</th><th>Min</th><th>Expected</th>
                                <th>Status</th><th>Avg Cost</th><th>Total Value</th><th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filtered.length === 0 && <tr><td colSpan={11} className="text-center text-muted py-8">No materials found.</td></tr>}
                            {filtered.map(r => {
                                const risk = calcRisk(r)
                                return (
                                    <tr key={r.id}>
                                        <td><strong>{r.code}</strong></td>
                                        <td>{r.description}</td>
                                        <td>{(r as any).supplier?.name ?? 'N/A'}</td>
                                        <td>
                                            <button onClick={() => setViewBatches(r.id)} className="text-navy font-semibold hover:underline decoration-dotted underline-offset-4">
                                                {r.stock} <i className="fas fa-layer-group text-[10px] ml-1 opacity-50" />
                                            </button>
                                        </td>
                                        <td>{r.demand}</td>
                                        <td>{r.min_stock}</td>
                                        <td>{r.on_order}</td>
                                        <td><span className={RISK_BADGE[risk]}>{risk}</span></td>
                                        <td>R{Number(r.avg_cost).toFixed(2)}</td>
                                        <td>R{(r.stock * r.avg_cost).toFixed(2)}</td>
                                        <td>
                                            <div className="flex gap-1">
                                                <button className="btn btn-sm btn-outline" onClick={() => openEdit(r)}>Edit</button>
                                                <button className="btn btn-sm btn-danger" onClick={() => handleDelete(r.id)}>Del</button>
                                            </div>
                                        </td>
                                    </tr>
                                )
                            })}
                        </tbody>
                    </table>
                </div>
            </div>

            {modalOpen && (
                <div className="modal-backdrop" onClick={e => e.target === e.currentTarget && close()}>
                    <div className="modal-box max-w-xl">
                        <div className="modal-header">
                            <h3 className="text-lg font-semibold text-navy">{editItem ? 'Edit Material' : 'Add Material'}</h3>
                            <button onClick={close} className="btn btn-ghost btn-sm"><i className="fas fa-times" /></button>
                        </div>
                        <form onSubmit={handleSubmit}>
                            <input type="hidden" name="id" value={editItem?.id ?? ''} />
                            <div className="modal-body grid grid-cols-2 gap-4">
                                <div><label className="form-label">Code *</label>
                                    <input name="code" className="form-input" required defaultValue={editItem?.code} /></div>
                                <div><label className="form-label">Description *</label>
                                    <input name="description" className="form-input" required defaultValue={editItem?.description} /></div>
                                <div><label className="form-label">Category</label>
                                    <input name="category" className="form-input" defaultValue={editItem?.category ?? 'Default'} /></div>
                                <div><label className="form-label">Preferred Supplier</label>
                                    <select name="supplier_id" className="form-select" defaultValue={editItem?.supplier_id ?? ''}>
                                        <option value="">None</option>
                                        {suppliers.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                                    </select></div>
                                <div><label className="form-label">Min Stock</label>
                                    <input type="number" name="min_stock" className="form-input" step="0.0001" min="0" defaultValue={editItem?.min_stock ?? 0} /></div>
                                <div><label className="form-label">Lead Time (days)</label>
                                    <input type="number" name="lead_days" className="form-input" min="0" defaultValue={editItem?.lead_days ?? 0} /></div>
                                <div><label className="form-label">Current Avg Cost (R)</label>
                                    <input type="number" name="avg_cost" className="form-input" step="0.01" min="0" defaultValue={editItem?.avg_cost ?? 0} /></div>
                                <div className="col-span-2 text-xs text-muted">Note: Updating cost here sets the baseline; actual cost is tracked via Batches.</div>
                            </div>
                            <div className="modal-footer">
                                <button type="button" onClick={close} className="btn btn-ghost">Cancel</button>
                                <button type="submit" className="btn btn-primary" disabled={isPending}>Save</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {viewBatches && (
                <div className="modal-backdrop" onClick={() => setViewBatches(null)}>
                    <div className="modal-box max-w-md">
                        <div className="modal-header">
                            <h3 className="text-lg font-semibold text-navy">Inventory Batches — {rawMaterials.find(r => r.id === viewBatches)?.code}</h3>
                            <button onClick={() => setViewBatches(null)} className="btn btn-ghost btn-sm"><i className="fas fa-times" /></button>
                        </div>
                        <div className="modal-body">
                            <table className="w-full text-sm">
                                <thead className="border-b text-muted font-semibold">
                                    <tr><th className="text-left pb-2">Batch #</th><th className="text-left pb-2">Location</th><th className="text-right pb-2">Qty</th></tr>
                                </thead>
                                <tbody className="divide-y">
                                    {itemBatches.length === 0 && <tr><td colSpan={3} className="text-center py-4 text-muted">No specific batches found.</td></tr>}
                                    {itemBatches.map(b => (
                                        <tr key={b.id} className="hover:bg-gray-50">
                                            <td className="py-2.5 font-medium">{b.batch_number}</td>
                                            <td className="py-2.5">{b.location?.name ?? 'Unknown'}</td>
                                            <td className="py-2.5 text-right font-semibold">{b.quantity}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                        <div className="modal-footer">
                            <button onClick={() => setViewBatches(null)} className="btn btn-primary w-full">Close</button>
                        </div>
                    </div>
                </div>
            )}
        </>
    )
}
