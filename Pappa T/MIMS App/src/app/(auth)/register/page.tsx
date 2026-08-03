'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { createClient } from '@/lib/supabase/client'

export default function RegisterPage() {
    const router = useRouter()
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [confirm, setConfirm] = useState('')
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)
    const [success, setSuccess] = useState(false)

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault()
        setError('')
        if (password !== confirm) { setError('Passwords do not match'); return }
        setLoading(true)
        const supabase = createClient()
        const { error } = await supabase.auth.signUp({ email, password })
        if (error) {
            setError(error.message)
            setLoading(false)
        } else {
            setSuccess(true)
            setTimeout(() => router.push('/login'), 3000)
        }
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 p-8">
            <div className="w-full max-w-md">
                <div className="text-center mb-6">
                    <i className="fas fa-industry text-4xl text-primary mb-2" />
                    <h1 className="text-2xl font-bold text-navy">MIMS ERP</h1>
                </div>

                <div className="bg-white rounded-2xl shadow-card p-8">
                    <h2 className="text-xl font-bold text-navy mb-1">Create your workspace</h2>
                    <p className="text-muted text-sm mb-6">Free — your data, your control.</p>

                    {success ? (
                        <div className="text-center py-6">
                            <i className="fas fa-check-circle text-5xl text-success mb-4" />
                            <p className="text-navy font-semibold">Account created!</p>
                            <p className="text-muted text-sm mt-1">Check your email to confirm, then sign in.</p>
                        </div>
                    ) : (
                        <>
                            {error && (
                                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                                    <i className="fas fa-exclamation-circle mr-2" />{error}
                                </div>
                            )}
                            <form onSubmit={handleSubmit} className="space-y-4">
                                <div>
                                    <label className="form-label">Email address</label>
                                    <input type="email" className="form-input" placeholder="you@company.com"
                                        value={email} onChange={e => setEmail(e.target.value)} required />
                                </div>
                                <div>
                                    <label className="form-label">Password</label>
                                    <input type="password" className="form-input" placeholder="Min. 6 characters"
                                        value={password} onChange={e => setPassword(e.target.value)} required minLength={6} />
                                </div>
                                <div>
                                    <label className="form-label">Confirm Password</label>
                                    <input type="password" className="form-input" placeholder="Repeat password"
                                        value={confirm} onChange={e => setConfirm(e.target.value)} required />
                                </div>
                                <button type="submit" className="btn btn-primary w-full py-2.5 mt-2" disabled={loading}>
                                    {loading ? <i className="fas fa-spinner fa-spin" /> : <i className="fas fa-user-plus" />}
                                    {loading ? 'Creating…' : 'Create Account'}
                                </button>
                            </form>
                        </>
                    )}

                    <p className="text-center text-sm text-muted mt-6">
                        Already have an account?{' '}
                        <Link href="/login" className="text-primary font-medium hover:underline">Sign in</Link>
                    </p>
                </div>
            </div>
        </div>
    )
}
