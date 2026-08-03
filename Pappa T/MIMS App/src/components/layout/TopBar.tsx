'use client'

import { useState } from 'react'

interface TopBarProps {
    pageTitle: string
}

const CURRENCIES = [
    { code: 'ZAR', symbol: 'R' },
    { code: 'USD', symbol: '$' },
    { code: 'EUR', symbol: '€' },
    { code: 'GBP', symbol: '£' },
]

export default function TopBar({ pageTitle }: TopBarProps) {
    const [currency, setCurrency] = useState('ZAR')

    function handleChange(e: React.ChangeEvent<HTMLSelectElement>) {
        setCurrency(e.target.value)
        if (typeof window !== 'undefined') {
            window.dispatchEvent(new CustomEvent('currency-change', { detail: e.target.value }))
        }
    }

    return (
        <header className="flex items-center justify-between mb-7 pb-4 border-b border-gray-200">
            <h2 className="text-2xl font-bold text-navy">{pageTitle}</h2>
            <div className="flex items-center gap-4">
                <div className="flex items-center gap-2 text-sm">
                    <label className="font-medium text-gray-600">Currency:</label>
                    <select
                        value={currency}
                        onChange={handleChange}
                        className="border border-gray-300 rounded-lg px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-primary/40"
                    >
                        {CURRENCIES.map(c => (
                            <option key={c.code} value={c.code}>{c.code} ({c.symbol})</option>
                        ))}
                    </select>
                </div>
                <div className="bg-emerald-100 text-emerald-700 text-xs font-semibold px-3 py-1 rounded-full">
                    ● Live
                </div>
            </div>
        </header>
    )
}
