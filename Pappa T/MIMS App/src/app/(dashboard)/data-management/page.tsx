'use client'

import { useState, useTransition, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { loadDemoDataAction, clearAllDataAction, checkSchemaAction } from '@/lib/actions/data-management'

export default function DataManagementPage() {
    const router = useRouter()
    const [isPending, startTransition] = useTransition()
    const [schemaOk, setSchemaOk] = useState<boolean | null>(null)
    const [toast, setToast] = useState<{ msg: string; type: 'success' | 'error' } | null>(null)

    useEffect(() => {
        checkSchemaAction().then(res => setSchemaOk(res.ok))
    }, [])

    function showToast(msg: string, type: 'success' | 'error' = 'success') {
        setToast({ msg, type }); setTimeout(() => setToast(null), 4000)
    }

    async function loadDemoData() {
        const result = await loadDemoDataAction()
        if (result?.error) {
            showToast(`Error: ${result.error}`, 'error')
            const check = await checkSchemaAction()
            setSchemaOk(check.ok)
        } else {
            router.refresh()
            showToast('✅ Demo data loaded! Test flow: Receive PO-1001 → Complete WO-1001 → Dispatch SO-1002')
        }
    }

    async function clearAllData() {
        if (!confirm('WARNING: Delete ALL your data? This cannot be undone.')) return
        const result = await clearAllDataAction()
        if (result?.error) {
            showToast(`Error: ${result.error}`, 'error')
        } else {
            router.refresh()
            showToast('All data cleared', 'error')
        }
    }

    return (
        <>
            {toast && (
                <div className={`fixed bottom-5 right-5 px-4 py-3 rounded-xl text-white font-medium text-sm shadow-dropdown z-[9999] animate-slide-in max-w-sm
          ${toast.type === 'error' ? 'bg-danger' : 'bg-success'}`}>{toast.msg}</div>
            )}

            {schemaOk === false && (
                <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3">
                    <i className="fas fa-exclamation-triangle text-red-500 mt-1" />
                    <div>
                        <h4 className="font-bold text-red-800 text-sm">Advanced Manufacturing Features: Database Sync Required</h4>
                        <p className="text-xs text-red-700 mt-1">The `locations` table was not found. Please run the migration script in your Supabase SQL Editor to enable enhanced inventory Tracking.</p>
                        <p className="text-[10px] text-red-600 mt-2 font-mono bg-red-100/50 p-2 rounded">File: COMPLETE_SUPABASE_MIGRATION.sql (Project Root)</p>
                    </div>
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div className="card bg-blue-50 border border-blue-200">
                    <h4 className="font-bold text-navy mb-2"><i className="fas fa-database mr-2 text-blue-500" />Load Demo Data</h4>
                    <p className="text-sm text-gray-600 mb-4">Populate all modules with sample data for testing the full MRP workflow.</p>
                    <button onClick={() => startTransition(loadDemoData)} disabled={isPending} className="btn btn-primary w-full">
                        {isPending ? <i className="fas fa-spinner fa-spin" /> : <i className="fas fa-database" />} Load Data
                    </button>
                </div>

                <div className="card bg-red-50 border border-red-200">
                    <h4 className="font-bold text-navy mb-2"><i className="fas fa-trash-alt mr-2 text-red-500" />Clear All Data</h4>
                    <p className="text-sm text-gray-600 mb-4">Permanently delete all your MIMS data. This action cannot be undone.</p>
                    <button onClick={() => startTransition(clearAllData)} disabled={isPending} className="btn btn-danger w-full">
                        <i className="fas fa-trash-alt" /> Clear All Data
                    </button>
                </div>

                <div className="card bg-yellow-50 border border-yellow-200">
                    <h4 className="font-bold text-navy mb-2"><i className="fas fa-download mr-2 text-yellow-600" />Export Data</h4>
                    <p className="text-sm text-gray-600 mb-4">Export your data to CSV. (Coming in a future release.)</p>
                    <button disabled className="btn w-full bg-gray-200 text-gray-500 cursor-not-allowed">
                        <i className="fas fa-download" /> Export CSV
                    </button>
                </div>
            </div>

            <div className="card">
                <h4 className="font-semibold text-navy mb-3">System Information</h4>
                <table className="text-sm w-full">
                    <tbody>
                        <tr className="border-b border-gray-100"><td className="py-2 text-muted">Database</td><td className="py-2 font-medium">Supabase PostgreSQL (live)</td></tr>
                        <tr className="border-b border-gray-100"><td className="py-2 text-muted">Framework</td><td className="py-2 font-medium">Next.js 14 (App Router)</td></tr>
                        <tr className="border-b border-gray-100"><td className="py-2 text-muted">Auth</td><td className="py-2 font-medium">Supabase Auth (per-user RLS)</td></tr>
                        <tr><td className="py-2 text-muted">Version</td><td className="py-2 font-medium">MIMS ERP v2.0</td></tr>
                    </tbody>
                </table>
            </div>
        </>
    )
}
