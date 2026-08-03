'use client'

import { useState, useTransition } from 'react'
import { upsertSupplier, deleteSupplier } from '@/lib/actions/suppliers'
import type { Supplier } from '@/lib/types'
import { useRouter } from 'next/navigation'

interface Props { suppliers: Supplier[] }

export default function SuppliersClient({ suppliers }: Props) {
    const router = useRouter()
    const [isPending, startTransition] = useTransition()
    const [modalOpen, setModalOpen] = useState(false)
    const [editItem, setEditItem] = useState<Supplier | null>(null)
    const [toast, setToast] = useState<string | null>(null)

    function showToast(msg: string) { setToast(msg); setTimeout(() => setToast(null), 3000) }

    function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
        e.preventDefault()
        const fd = new FormData(e.currentTarget)
        startTransition(async () => {
            await upsertSupplier(fd)
            router.refresh()
            setModalOpen(false)
            showToast(editItem ? 'Supplier updated' : 'Supplier added')
        })
    }

    function handleDelete(id: string) {
        if (!confirm('Delete this supplier?')) return
        startTransition(async () => {
            await deleteSupplier(id)
            router.refresh()
            showToast('Supplier deleted')
        })
    }

    return (
        <>
            {toast && <div className="fixed bottom-5 right-5 px-4 py-3 rounded-xl text-white font-medium text-sm bg-success shadow-dropdown z-[9999] animate-slide-in">{toast}</div>}

            <div className="card">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-navy">Suppliers</h3>
                    <button onClick={() => { setEditItem(null); setModalOpen(true) }} className="btn btn-primary">
                        <i className="fas fa-plus" /> Add Supplier
                    </button>
                </div>
                <div className="table-wrap">
                    <table className="data-table">
                        <thead><tr><th>Company</th><th>Contact</th><th>Email</th><th>Phone</th><th>Actions</th></tr></thead>
                        <tbody>
                            {suppliers.length === 0 && <tr><td colSpan={5} className="text-center text-muted py-8">No suppliers yet.</td></tr>}
                            {suppliers.map(s => (
                                <tr key={s.id}>
                                    <td><strong>{s.name}</strong></td>
                                    <td>{s.contact}</td>
                                    <td>{s.email}</td>
                                    <td>{s.phone}</td>
                                    <td><div className="flex gap-1">
                                        <button className="btn btn-sm btn-outline" onClick={() => { setEditItem(s); setModalOpen(true) }}>Edit</button>
                                        <button className="btn btn-sm btn-danger" onClick={() => handleDelete(s.id)}>Del</button>
                                    </div></td>
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
                            <h3 className="text-lg font-semibold text-navy">{editItem ? 'Edit Supplier' : 'Add Supplier'}</h3>
                            <button onClick={() => setModalOpen(false)} className="btn btn-ghost btn-sm"><i className="fas fa-times" /></button>
                        </div>
                        <form onSubmit={handleSubmit}>
                            <input type="hidden" name="id" value={editItem?.id ?? ''} />
                            <div className="modal-body space-y-4">
                                <div><label className="form-label">Company Name *</label>
                                    <input name="name" className="form-input" required defaultValue={editItem?.name} /></div>
                                <div><label className="form-label">Contact Person</label>
                                    <input name="contact" className="form-input" defaultValue={editItem?.contact ?? ''} /></div>
                                <div><label className="form-label">Email</label>
                                    <input type="email" name="email" className="form-input" defaultValue={editItem?.email ?? ''} /></div>
                                <div><label className="form-label">Phone</label>
                                    <input name="phone" className="form-input" defaultValue={editItem?.phone ?? ''} /></div>
                            </div>
                            <div className="modal-footer">
                                <button type="button" onClick={() => setModalOpen(false)} className="btn btn-ghost">Cancel</button>
                                <button type="submit" className="btn btn-primary" disabled={isPending}>
                                    {isPending ? <i className="fas fa-spinner fa-spin" /> : null} Save
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </>
    )
}
