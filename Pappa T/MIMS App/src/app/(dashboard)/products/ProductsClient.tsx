'use client'

import { useState, useTransition } from 'react'
import { upsertItem, deleteItem } from '@/lib/actions/items'
import { calcRisk, type FinishedGood as Item, type RawMaterial as Component } from '@/lib/types'
import { useRouter } from 'next/navigation'

interface Props { 
    finishedGoods: Item[]; 
    rawMaterials: Component[];
    batches: any[]
}

const RISK_BADGE: Record<string, string> = {
    'R1': 'badge badge-r1', 'Medium Risk': 'badge badge-medium', 'High Risk': 'badge badge-high',
}

interface BomRow { component_item_id: string; qty_per_unit: number }

export default function ProductsClient({ finishedGoods, rawMaterials, batches }: Props) {
    const router = useRouter()
    const [isPending, startTransition] = useTransition()
    const [search, setSearch] = useState('')
    const [modalOpen, setModalOpen] = useState(false)
    const [viewBatches, setViewBatches] = useState<string | null>(null)
    const [editItem, setEditItem] = useState<Item | null>(null)
    const [bom, setBom] = useState<BomRow[]>([])
    const [toast, setToast] = useState<string | null>(null)

    const filtered = finishedGoods.filter(f =>
        `${f.code} ${f.description} ${f.category}`.toLowerCase().includes(search.toLowerCase())
    )

    function showToast(msg: string) { setToast(msg); setTimeout(() => setToast(null), 3000) }
    function close() { setModalOpen(false) }

    function openAdd() {
        setEditItem(null); setBom([]); setModalOpen(true)
    }
    function openEdit(f: Item) {
        setEditItem(f)
        setBom((f as any).bom_items?.map((b: any) => ({ component_item_id: b.component_item_id, qty_per_unit: b.qty_per_unit })) ?? [])
        setModalOpen(true)
    }

    function addBomRow() { setBom(prev => [...prev, { component_item_id: '', qty_per_unit: 1 }]) }
    function removeBomRow(i: number) { setBom(prev => prev.filter((_, idx) => idx !== i)) }
    function updateBomRow(i: number, field: keyof BomRow, val: string | number) {
        setBom(prev => prev.map((r, idx) => idx === i ? { ...r, [field]: val } : r))
    }

    // Material cost calculation (simple sum of direct components)
    // Real recursive cost is handled via RPC get_bom_cost but for UI feedback we use direct components
    const directBomCost = bom.reduce((s, b) => {
        const comp = rawMaterials.find(r => r.id === b.component_item_id)
        return s + b.qty_per_unit * (comp?.avg_cost ?? 0)
    }, 0)

    function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
        e.preventDefault()
        const fd = new FormData(e.currentTarget)
        fd.set('type', fd.get('type') || 'Product') // Default to Product
        fd.set('bom', JSON.stringify(bom.filter(b => b.component_item_id)))
        startTransition(async () => {
            await upsertItem(fd)
            router.refresh()
            close()
            showToast(editItem ? 'Item updated' : 'Item added')
        })
    }

    function handleDelete(id: string) {
        if (!confirm('Delete this item?')) return
        startTransition(async () => {
            await deleteItem(id)
            router.refresh()
            showToast('Item deleted')
        })
    }

    return (
        <>
            {toast && <div className="fixed bottom-5 right-5 px-4 py-3 rounded-xl text-white font-medium text-sm bg-success shadow-dropdown z-[9999] animate-slide-in">{toast}</div>}

            <div className="card">
                <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
                    <div className="flex items-center gap-3">
                        <h3 className="text-lg font-semibold text-navy">Products & Sub-Assemblies</h3>
                        <input type="text" placeholder="Search…" value={search} onChange={e => setSearch(e.target.value)}
                            className="form-input w-52 text-sm py-1.5" />
                    </div>
                    <button onClick={openAdd} className="btn btn-primary"><i className="fas fa-plus" /> Add Item</button>
                </div>
                <div className="table-wrap">
                    <table className="data-table">
                        <thead><tr>
                            <th>Code</th><th>Description</th><th>Type</th><th>Est. COGS</th>
                            <th>On Hand</th><th>Committed</th><th>Min</th>
                            <th>Lead</th><th>Status</th><th>Sales Price</th><th>Total Value</th><th>Actions</th>
                        </tr></thead>
                        <tbody>
                            {filtered.length === 0 && <tr><td colSpan={13} className="text-center text-muted py-8">No items found.</td></tr>}
                            {filtered.map(f => {
                                const risk = calcRisk({ stock: f.stock, demand: f.demand, min_stock: f.min_stock, on_order: 0 })
                                return (
                                    <tr key={f.id}>
                                        <td><strong>{f.code}</strong></td>
                                        <td>{f.description}</td>
                                        <td><span className="badge badge-outline">{f.type}</span></td>
                                        <td>R{Number(f.avg_cost).toFixed(2)}</td>
                                        <td>
                                            <button onClick={() => setViewBatches(f.id)} className="text-navy font-semibold hover:underline decoration-dotted underline-offset-4">
                                                {f.stock} <i className="fas fa-layer-group text-[10px] ml-1 opacity-50" />
                                            </button>
                                        </td>
                                        <td>{f.demand}</td>
                                        <td>{f.min_stock}</td>
                                        <td>{f.lead_days}d</td>
                                        <td><span className={RISK_BADGE[risk]}>{risk}</span></td>
                                        <td>R{Number(f.sales_price).toFixed(2)}</td>
                                        <td>R{(f.stock * (f.avg_cost ?? 0)).toFixed(2)}</td>
                                        <td><div className="flex gap-1">
                                            <button className="btn btn-sm btn-outline" onClick={() => openEdit(f)}>Edit</button>
                                            <button className="btn btn-sm btn-danger" onClick={() => handleDelete(f.id)}>Del</button>
                                        </div></td>
                                    </tr>
                                )
                            })}
                        </tbody>
                    </table>
                </div>
            </div>

            {modalOpen && (
                <div className="modal-backdrop" onClick={e => e.target === e.currentTarget && close()}>
                    <div className="modal-box max-w-2xl">
                        <div className="modal-header">
                            <h3 className="text-lg font-semibold text-navy">{editItem ? 'Edit Item' : 'Add Item'}</h3>
                            <button onClick={close} className="btn btn-ghost btn-sm"><i className="fas fa-times" /></button>
                        </div>
                        <form onSubmit={handleSubmit}>
                            <input type="hidden" name="id" value={editItem?.id ?? ''} />
                            <div className="modal-body">
                                <div className="grid grid-cols-2 gap-4 mb-5">
                                    <div><label className="form-label">Code *</label>
                                        <input name="code" className="form-input" required defaultValue={editItem?.code} /></div>
                                    <div><label className="form-label">Description *</label>
                                        <input name="description" className="form-input" required defaultValue={editItem?.description} /></div>
                                    <div><label className="form-label">Item Type</label>
                                        <select name="type" className="form-select" defaultValue={editItem?.type ?? 'Product'}>
                                            <option value="Product">Product</option>
                                            <option value="Sub-Assembly">Sub-Assembly</option>
                                        </select></div>
                                    <div><label className="form-label">Category</label>
                                        <input name="category" className="form-input" defaultValue={editItem?.category ?? 'Default'} /></div>
                                    <div className="col-span-2 grid grid-cols-3 gap-4">
                                        <div><label className="form-label">Sales Price (R)</label>
                                            <input type="number" name="sales_price" className="form-input" step="0.01" min="0" defaultValue={editItem?.sales_price ?? 0} /></div>
                                        <div><label className="form-label">Min Stock</label>
                                            <input type="number" name="min_stock" className="form-input" step="0.0001" min="0" defaultValue={editItem?.min_stock ?? 0} /></div>
                                        <div><label className="form-label">Lead Time (days)</label>
                                            <input type="number" name="lead_days" className="form-input" min="0" defaultValue={editItem?.lead_days ?? 0} /></div>
                                    </div>
                                </div>

                                {/* BOM */}
                                <div className="border border-gray-200 rounded-xl p-4 bg-gray-50">
                                    <div className="flex items-center justify-between mb-3">
                                        <h4 className="font-semibold text-navy text-sm">Bill of Materials</h4>
                                        <button type="button" onClick={addBomRow} className="btn btn-sm btn-outline">
                                            <i className="fas fa-plus" /> Add Component
                                        </button>
                                    </div>
                                    <div className="grid grid-cols-12 text-xs font-semibold text-muted mb-2 border-b pb-1">
                                        <div className="col-span-7">Component</div><div className="col-span-4">Qty / Unit</div><div className="col-span-1"></div>
                                    </div>
                                    {bom.map((row, i) => (
                                        <div key={i} className="grid grid-cols-12 gap-2 mb-2 items-center">
                                            <div className="col-span-7">
                                                <select className="form-select text-sm" value={row.component_item_id} onChange={e => updateBomRow(i, 'component_item_id', e.target.value)}>
                                                    <option value="">Select Component</option>
                                                    {rawMaterials.map(r => <option key={r.id} value={r.id}>{editItem?.id !== r.id && `[${r.type}] ${r.code} — ${r.description}`}</option>)}
                                                    {finishedGoods.map(r => <option key={r.id} value={r.id}>{editItem?.id !== r.id && `[${r.type}] ${r.code} — ${r.description}`}</option>)}
                                                </select>
                                            </div>
                                            <div className="col-span-4">
                                                <input type="number" className="form-input text-sm" step="0.0001" min="0.0001"
                                                    value={row.qty_per_unit} onChange={e => updateBomRow(i, 'qty_per_unit', parseFloat(e.target.value))} />
                                            </div>
                                            <div className="col-span-1">
                                                <button type="button" onClick={() => removeBomRow(i)} className="btn btn-sm btn-danger">
                                                    <i className="fas fa-times" />
                                                </button>
                                            </div>
                                        </div>
                                    ))}
                                    <p className="text-sm font-semibold mt-2 text-navy">Direct Component Cost: R{directBomCost.toFixed(2)}</p>
                                    <p className="text-[10px] text-muted italic">Recursive costs are calculated when items are received or produced.</p>
                                </div>
                            </div>
                            <div className="modal-footer">
                                <button type="button" onClick={close} className="btn btn-ghost">Cancel</button>
                                <button type="submit" className="btn btn-primary" disabled={isPending}>
                                    {isPending ? <i className="fas fa-spinner fa-spin" /> : null} Save
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
            {viewBatches && (
                <div className="modal-backdrop" onClick={() => setViewBatches(null)}>
                    <div className="modal-box max-w-md">
                        <div className="modal-header">
                            <h3 className="text-lg font-semibold text-navy">Inventory Batches — {finishedGoods.find(f => f.id === viewBatches)?.code}</h3>
                            <button onClick={() => setViewBatches(null)} className="btn btn-ghost btn-sm"><i className="fas fa-times" /></button>
                        </div>
                        <div className="modal-body">
                            <table className="w-full text-sm">
                                <thead className="border-b text-muted font-semibold">
                                    <tr><th className="text-left pb-2">Batch #</th><th className="text-left pb-2">Location</th><th className="text-right pb-2">Qty</th></tr>
                                </thead>
                                <tbody className="divide-y">
                                    {(batches.filter((b: any) => b.item_id === viewBatches)).length === 0 && <tr><td colSpan={3} className="text-center py-4 text-muted">No specific batches found.</td></tr>}
                                    {batches.filter((b: any) => b.item_id === viewBatches).map((b: any) => (
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
