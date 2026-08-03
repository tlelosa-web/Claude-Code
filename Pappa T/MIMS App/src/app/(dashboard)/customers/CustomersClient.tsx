'use client'

import { useState, useTransition } from 'react'
import { upsertCustomer, deleteCustomer } from '@/lib/actions/customers'
import type { Customer } from '@/lib/types'
import { useRouter } from 'next/navigation'

interface Props { customers: Customer[] }

export default function CustomersClient({ customers }: Props) {
    const router = useRouter()
    const [isPending, startTransition] = useTransition()
    const [modalOpen, setModalOpen] = useState(false)
    const [editItem, setEditItem] = useState<Customer | null>(null)
    const [toast, setToast] = useState<string | null>(null)

    function showToast(msg: string) { setToast(msg); setTimeout(() => setToast(null), 3000) }

    function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
        e.preventDefault()
        const fd = new FormData(e.currentTarget)
        startTransition(async () => {
            await upsertCustomer(fd)
            router.refresh()
            setModalOpen(false)
            showToast(editItem ? 'Customer updated' : 'Customer added')
        })
    }

    function handleDelete(id: string) {
        if (!confirm('Delete this customer?')) return
        startTransition(async () => {
            await deleteCustomer(id)
            router.refresh()
            showToast('Customer deleted')
        })
    }

    return (
        <>
            {toast && <div className="fixed bottom-5 right-5 px-4 py-3 rounded-xl text-white font-medium text-sm bg-success shadow-dropdown z-[9999] animate-slide-in">{toast}</div>}

            <div className="card">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-navy">Customers</h3>
                    <button onClick={() => { setEditItem(null); setModalOpen(true) }} className="btn btn-primary">
                        <i className="fas fa-plus" /> Add Customer
                    </button>
                </div>
                <div className="table-wrap">
                    <table className="data-table">
                        <thead><tr><th>Company</th><th>Contact</th><th>Email</th><th>City</th><th>Actions</th></tr></thead>
                        <tbody>
                            {customers.length === 0 && <tr><td colSpan={5} className="text-center text-muted py-8">No customers yet.</td></tr>}
                            {customers.map(c => (
                                <tr key={c.id}>
                                    <td><strong>{c.name}</strong></td>
                                    <td>{c.contact}</td>
                                    <td>{c.email}</td>
                                    <td>{c.city}</td>
                                    <td><div className="flex gap-1">
                                        <button className="btn btn-sm btn-outline" onClick={() => { setEditItem(c); setModalOpen(true) }}>Edit</button>
                                        <button className="btn btn-sm btn-danger" onClick={() => handleDelete(c.id)}>Del</button>
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
                            <h3 className="text-lg font-semibold text-navy">{editItem ? 'Edit Customer' : 'Add Customer'}</h3>
                            <button onClick={() => setModalOpen(false)} className="btn btn-ghost btn-sm"><i className="fas fa-times" /></button>
                        </div>
                        <form onSubmit={handleSubmit}>
                            <input type="hidden" name="id" value={editItem?.id ?? ''} />
                            <div className="modal-body space-y-4">
                                <div><label className="form-label">Company Name *</label>
                                    <input name="name" className="form-input" required defaultValue={editItem?.name} /></div>
                                <div><label className="form-label">Contact Person *</label>
                                    <input name="contact" className="form-input" required defaultValue={editItem?.contact ?? ''} /></div>
                                <div><label className="form-label">Email *</label>
                                    <input type="email" name="email" className="form-input" required defaultValue={editItem?.email ?? ''} /></div>
                                <div><label className="form-label">City</label>
                                    <input name="city" className="form-input" defaultValue={editItem?.city ?? ''} /></div>
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
