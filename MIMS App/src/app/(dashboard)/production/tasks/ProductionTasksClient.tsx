'use client'

import { useState, useTransition } from 'react'
import { updateProductionTaskStatus } from '@/lib/actions/production'

interface Props {
    tasks: any[]
}

const STATUS_COLOR: Record<string, string> = {
    'Pending': 'badge',
    'In Progress': 'badge badge-ordered',
    'Completed': 'badge badge-received',
    'Paused': 'badge badge-cancelled'
}

export default function ProductionTasksClient({ tasks }: Props) {
    const [isPending, startTransition] = useTransition()
    const [completeModal, setCompleteModal] = useState<{ id: string; op: string } | null>(null)
    const [minutes, setMinutes] = useState<number>(0)
    const [toast, setToast] = useState<{ msg: string; type: 'success' | 'error' } | null>(null)

    function showToast(msg: string, type: 'success' | 'error' = 'success') {
        setToast({ msg, type }); setTimeout(() => setToast(null), 3500)
    }

    function doStart(id: string) {
        startTransition(async () => {
            try {
                await updateProductionTaskStatus(id, 'In Progress')
                window.location.reload()
            } catch (e: any) {
                showToast(e.message ?? 'Error', 'error')
            }
        })
    }

    function doComplete(e: React.FormEvent<HTMLFormElement>) {
        e.preventDefault()
        if (!completeModal) return
        startTransition(async () => {
            try {
                await updateProductionTaskStatus(completeModal.id, 'Completed', minutes)
                setCompleteModal(null)
                window.location.reload()
            } catch (e: any) {
                showToast(e.message ?? 'Error', 'error')
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
                    <h3 className="text-lg font-semibold text-navy">Operator Tasks</h3>
                </div>
                <div className="table-wrap">
                    <table className="data-table">
                        <thead><tr>
                            <th>Order</th><th>Item</th><th>Operation</th><th>Work Center</th>
                            <th>Seq</th><th>Status</th><th>Started</th><th>Actions</th>
                        </tr></thead>
                        <tbody>
                            {tasks.length === 0 && <tr><td colSpan={8} className="text-center text-muted py-8">No tasks assigned.</td></tr>}
                            {tasks.map((t: any) => (
                                <tr key={t.id}>
                                    <td>{t.order?.order_number ?? '—'}</td>
                                    <td>{t.order?.item?.code ?? '—'}</td>
                                    <td className="font-medium">{t.operation_name}</td>
                                    <td>{t.work_center?.name ?? '—'}</td>
                                    <td>{t.sequence_order}</td>
                                    <td><span className={STATUS_COLOR[t.status] ?? 'badge'}>{t.status}</span></td>
                                    <td>{t.started_at ? new Date(t.started_at).toLocaleString() : '—'}</td>
                                    <td>
                                        <div className="flex gap-1">
                                            {t.status === 'Pending' && (
                                                <button className="btn btn-sm btn-primary" onClick={() => doStart(t.id)} disabled={isPending}>
                                                    Start
                                                </button>
                                            )}
                                            {t.status !== 'Completed' && (
                                                <button className="btn btn-sm btn-success"
                                                    onClick={() => { setMinutes(0); setCompleteModal({ id: t.id, op: t.operation_name }) }}
                                                    disabled={isPending}>
                                                    Complete
                                                </button>
                                            )}
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {completeModal && (
                <div className="modal-backdrop" onClick={() => setCompleteModal(null)}>
                    <div className="modal-box max-w-sm" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3 className="text-lg font-semibold text-navy">Complete Task: {completeModal.op}</h3>
                            <button onClick={() => setCompleteModal(null)} className="btn btn-ghost btn-sm"><i className="fas fa-times" /></button>
                        </div>
                        <form onSubmit={doComplete}>
                            <div className="modal-body space-y-4">
                                <div>
                                    <label className="form-label">Actual Time (minutes)</label>
                                    <input type="number" className="form-input" min={0} step={1} value={minutes}
                                           onChange={e => setMinutes(parseFloat(e.target.value))} />
                                </div>
                                <p className="text-[10px] text-muted">Labor cost will be calculated from work center rates.</p>
                            </div>
                            <div className="modal-footer">
                                <button type="button" onClick={() => setCompleteModal(null)} className="btn btn-ghost">Cancel</button>
                                <button type="submit" className="btn btn-success" disabled={isPending}>
                                    {isPending ? <i className="fas fa-spinner fa-spin" /> : null} Complete
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </>
    )
}
