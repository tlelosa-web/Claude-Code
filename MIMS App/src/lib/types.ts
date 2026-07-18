// ─────────────────────────────────────────────────────────────────
// MIMS ERP — Supabase TypeScript types
// ─────────────────────────────────────────────────────────────────

export interface Supplier {
    id: string
    user_id: string
    name: string
    contact: string | null
    email: string | null
    phone: string | null
    created_at: string
}

export interface Customer {
    id: string
    user_id: string
    name: string
    contact: string | null
    email: string | null
    city: string | null
    created_at: string
}

export interface RawMaterial {
    id: string
    user_id: string
    code: string
    description: string
    type: 'Material' | 'Product' | 'Sub-Assembly'
    category: string
    supplier_id: string | null
    stock: number
    demand: number
    min_stock: number
    on_order: number
    lead_days: number
    avg_cost: number
    sales_price?: number | null
    created_at: string
    // joined
    supplier?: Supplier | null
}

export interface BomItem {
    id: string
    user_id: string
    finished_good_id: string
    raw_material_id: string
    qty_per_unit: number
    // joined
    raw_material?: RawMaterial | null
}

export interface FinishedGood {
    id: string
    user_id: string
    code: string
    description: string
    type: 'Material' | 'Product' | 'Sub-Assembly'
    category: string
    stock: number
    demand: number
    min_stock: number
    in_production: number
    lead_days: number
    avg_cost: number
    sales_price: number | null
    created_at: string
    // joined
    bom_items?: BomItem[]
}

export type Item = RawMaterial | FinishedGood

export interface PurchaseOrder {
    id: string
    user_id: string
    order_number: string
    supplier_id: string | null
    status: 'Ordered' | 'Received' | 'Cancelled'
    delivery_date: string | null
    total: number
    created_at: string
    // joined
    supplier?: Supplier | null
    po_items?: PoItem[]
}

export interface PoItem {
    id: string
    user_id: string
    purchase_order_id: string
    raw_material_id: string | null
    quantity: number
    unit_cost: number
    // joined
    raw_material?: RawMaterial | null
}

export interface ProductionOrder {
    id: string
    user_id: string
    order_number: string
    finished_good_id: string | null
    quantity: number
    status: 'Pending' | 'In Progress' | 'Completed' | 'Cancelled'
    due_date: string | null
    created_at: string
    // joined
    finished_good?: FinishedGood | null
}

export interface SalesOrder {
    id: string
    user_id: string
    order_number: string
    customer_id: string | null
    status: 'Confirmed' | 'Ready for Dispatch' | 'Dispatched' | 'Cancelled'
    delivery_date: string | null
    created_at: string
    // joined
    customer?: Customer | null
    so_items?: SoItem[]
}

export interface SoItem {
    id: string
    user_id: string
    sales_order_id: string
    finished_good_id: string | null
    quantity: number
    unit_price: number
    // joined
    finished_good?: FinishedGood | null
}

// ─── Utility ─────────────────────────────────────────────────────

export type RiskLevel = 'R1' | 'Medium Risk' | 'High Risk'

export function calcRisk(item: { stock: number; demand: number; min_stock: number; on_order: number }): RiskLevel {
    const net = item.stock + item.on_order - item.demand
    if (net >= item.min_stock * 1.5) return 'R1'
    if (net >= item.min_stock) return 'Medium Risk'
    return 'High Risk'
}

export function calcBomCost(bomItems: BomItem[]): number {
    return bomItems.reduce((sum, b) => {
        return sum + b.qty_per_unit * (b.raw_material?.avg_cost ?? 0)
    }, 0)
}
