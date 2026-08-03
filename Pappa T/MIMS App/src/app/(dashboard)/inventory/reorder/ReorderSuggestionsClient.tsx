'use client'

interface Props {
    suggestions: { id: string; code: string; description: string; stock: number; on_order: number; min_stock: number; lead_days: number }[]
}

export default function ReorderSuggestionsClient({ suggestions }: Props) {
    return (
        <div className="card">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-navy">Items Below Minimum Stock</h3>
            </div>
            <div className="table-wrap">
                <table className="data-table">
                    <thead><tr>
                        <th>Code</th><th>Description</th><th>On Hand</th><th>On Order</th>
                        <th>Min</th><th>Lead (d)</th><th>Suggested Qty</th>
                    </tr></thead>
                    <tbody>
                        {suggestions.length === 0 && <tr><td colSpan={7} className="text-center text-muted py-8">No items need reordering.</td></tr>}
                        {suggestions.map(s => {
                            const suggested = Math.max(0, (s.min_stock ?? 0) - ((s.stock ?? 0) + (s.on_order ?? 0)))
                            return (
                                <tr key={s.id}>
                                    <td><strong>{s.code}</strong></td>
                                    <td>{s.description}</td>
                                    <td>{s.stock ?? 0}</td>
                                    <td>{s.on_order ?? 0}</td>
                                    <td>{s.min_stock ?? 0}</td>
                                    <td>{s.lead_days ?? 0}</td>
                                    <td className="font-semibold">{suggested}</td>
                                </tr>
                            )
                        })}
                    </tbody>
                </table>
            </div>
        </div>
    )
}
