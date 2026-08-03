'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { createClient } from '@/lib/supabase/client'

export default function LoginPage() {
    const router = useRouter()
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault()
        setError('')
        setLoading(true)
        const supabase = createClient()
        const { error } = await supabase.auth.signInWithPassword({ email, password })
        if (error) {
            setError(error.message)
            setLoading(false)
        } else {
            router.push('/')
            router.refresh()
        }
    }

    return (
        <div className="min-h-screen flex">
            {/* Left panel */}
            <div className="hidden lg:flex lg:w-1/2 items-center justify-center p-12"
                style={{ background: 'linear-gradient(135deg, #1d3557 0%, #3f37c9 100%)' }}>
                <div className="text-white text-center">
                    <i className="fas fa-industry text-6xl mb-6 text-emerald-400" />
                    <h1 className="text-4xl font-bold mb-3">MIMS ERP</h1>
                    <p className="text-white/70 text-lg max-w-xs">
                        Manufacturing & Inventory Management System — Production-ready, real-time, multi-user.
                    </p>
                </div>
            </div>

            {/* Right panel — form */}
            <div className="flex-1 flex items-center justify-center p-8 bg-gray-50">
                <div className="w-full max-w-md">
                    <div className="bg-white rounded-2xl shadow-card p-8">
                        <div className="mb-8">
                            <h2 className="text-2xl font-bold text-navy">Welcome back</h2>
                            <p className="text-muted text-sm mt-1">Sign in to your MIMS workspace</p>
                        </div>

                        {error && (
                            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                                <i className="fas fa-exclamation-circle mr-2" />{error}
                            </div>
                        )}

                        <form onSubmit={handleSubmit} className="space-y-5">
                            <div>
                                <label className="form-label">Email address</label>
                                <input
                                    type="email"
                                    className="form-input"
                                    placeholder="you@company.com"
                                    value={email}
                                    onChange={e => setEmail(e.target.value)}
                                    required
                                    autoComplete="email"
                                />
                            </div>
                            <div>
                                <label className="form-label">Password</label>
                                <input
                                    type="password"
                                    className="form-input"
                                    placeholder="••••••••"
                                    value={password}
                                    onChange={e => setPassword(e.target.value)}
                                    required
                                    autoComplete="current-password"
                                />
                            </div>
                            <button type="submit" className="btn btn-primary w-full py-2.5" disabled={loading}>
                                {loading ? <i className="fas fa-spinner fa-spin" /> : <i className="fas fa-sign-in-alt" />}
                                {loading ? 'Signing in…' : 'Sign In'}
                            </button>
                        </form>

                        <p className="text-center text-sm text-muted mt-6">
                            No account?{' '}
                            <Link href="/register" className="text-primary font-medium hover:underline">
                                Create one free
                            </Link>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )
}
