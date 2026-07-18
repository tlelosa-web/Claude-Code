'use server'

import { createClient } from '@/lib/supabase/server'
import { revalidatePath } from 'next/cache'

export async function checkSchemaAction() {
    const supabase = await createClient()
    const { error } = await supabase.from('locations').select('id').limit(1)
    return { ok: !error, error: error?.message }
}

export async function loadDemoDataAction() {
    const supabase = await createClient()
    
    // 1. Auth Verification
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) {
        console.error('[loadDemoDataAction] Unauthenticated')
        return { error: 'Unauthenticated' }
    }

    try {
        console.log('[loadDemoDataAction] Starting seed for user:', user.id)

        // 2. Locations (Idempotent / Robust)
        const { data: locs, error: locError } = await supabase.from('locations').insert([
            { user_id: user.id, name: 'Main Warehouse', is_default: true },
            { user_id: user.id, name: 'Shop Floor Bin A' }
        ]).select()

        if (locError) {
            console.error('[loadDemoDataAction] Loc Error:', locError.message)
            return { error: `Location creation failed: ${locError.message}` }
        }
        if (!locs || locs.length === 0) {
            console.error('[loadDemoDataAction] Loc Result is Null/Empty')
            return { error: 'Failed to create locations.' }
        }
        const l1 = locs[0].id

        // 3. Work Centers
        const { data: wcs, error: wcError } = await supabase.from('work_centers').insert([
            { user_id: user.id, name: 'Assembly Line 1', hourly_rate: 45.00 },
            { user_id: user.id, name: 'Testing Station', hourly_rate: 30.00 }
        ]).select()

        if (wcError || !wcs || wcs.length === 0) {
            console.error('[loadDemoDataAction] WC Error:', wcError?.message)
            return { error: 'Work center creation failed.' }
        }
        const wc1 = wcs[0].id

        // 4. Suppliers & Customers
        const { data: sup, error: supError } = await supabase.from('suppliers').insert([
            { user_id: user.id, name: 'Global Tech Components' },
            { user_id: user.id, name: 'Alloy & Metal Supplies' }
        ]).select()

        if (supError || !sup || sup.length === 0) {
            console.error('[loadDemoDataAction] Supplier Error:', supError?.message)
            return { error: 'Supplier creation failed.' }
        }
        const s1 = sup[0].id

        const { data: custs, error: custError } = await supabase.from('customers').insert([
            { user_id: user.id, name: 'Build-It Solutions', city: 'Johannesburg' }
        ]).select()

        if (custError || !custs || custs.length === 0) {
            console.error('[loadDemoDataAction] Customer Error:', custError?.message)
            return { error: 'Customer creation failed.' }
        }
        const c1 = custs[0].id

        // 5. Unified Items
        const { data: items, error: itemError } = await supabase.from('items').insert([
            { user_id: user.id, code: 'ALU-001', description: 'Aluminum Casting', type: 'Material', avg_cost: 12.50 },
            { user_id: user.id, code: 'CHIP-X', description: 'Logic Chip', type: 'Material', avg_cost: 8.75 },
            { user_id: user.id, code: 'SENS-MOD', description: 'Sensor Module', type: 'Sub-Assembly', sales_price: 75.00 },
            { user_id: user.id, code: 'CTRL-PNL', description: 'Control Panel', type: 'Product', sales_price: 150.00 }
        ]).select()

        if (itemError || !items || items.length < 4) {
            console.error('[loadDemoDataAction] Item Error:', itemError?.message)
            return { error: 'Item creation failed (duplicate codes?). Clear data first.' }
        }
        const [i1, i2, i3, i4] = items

        // 6. Initial Inventory (Seeding Stock via RPC)
        await (supabase.rpc as any)('adjust_inventory', { p_item_id: i1.id, p_location_id: l1, p_batch_number: 'B-ALU-01', p_qty: 500, p_cost: 12.50, p_user_id: user.id })
        await (supabase.rpc as any)('adjust_inventory', { p_item_id: i2.id, p_location_id: l1, p_batch_number: 'B-CHP-01', p_qty: 200, p_cost: 8.75, p_user_id: user.id })

        // 7. BOMs & Routings
        const { error: bomError } = await supabase.from('bom_items').insert([
            { user_id: user.id, parent_item_id: i3.id, component_item_id: i2.id, qty_per_unit: 2 },
            { user_id: user.id, parent_item_id: i4.id, component_item_id: i3.id, qty_per_unit: 1 },
            { user_id: user.id, parent_item_id: i4.id, component_item_id: i1.id, qty_per_unit: 3 }
        ])
        if (bomError) console.warn('[loadDemoDataAction] BOM insert issue:', bomError.message)

        await supabase.from('routings').insert([
            { user_id: user.id, item_id: i4.id, work_center_id: wc1, operation_name: 'Main Assembly', sequence_order: 1, standard_time_mins: 20 }
        ])

        // 8. Sample Workflow Orders
        // Purchase Order
        const { data: po } = await supabase.from('purchase_orders').insert({
            user_id: user.id, order_number: 'PO-1001', supplier_id: s1, status: 'Ordered', delivery_date: new Date().toISOString().split('T')[0]
        }).select().single()
        if (po) await supabase.from('po_items').insert({ user_id: user.id, purchase_order_id: po.id, item_id: i1.id, quantity: 100, unit_cost: 12.00 })

        // Production Order
        const { data: mo } = await supabase.from('production_orders').insert({
            user_id: user.id, order_number: 'WO-1001', item_id: i4.id, quantity: 20, status: 'Pending'
        }).select().single()
        if (mo) await (supabase.rpc as any)('create_production_tasks', { p_production_order_id: mo.id, p_user_id: user.id })

        // Sales Order
        const { data: so } = await supabase.from('sales_orders').insert({
            user_id: user.id, order_number: 'SO-1002', customer_id: c1, status: 'Ready for Dispatch'
        }).select().single()
        if (so) await supabase.from('so_items').insert({ user_id: user.id, sales_order_id: so.id, item_id: i4.id, quantity: 5, unit_price: 150.00 })

        console.log('[loadDemoDataAction] Seed complete')
        revalidatePath('/')
        return { success: true }

    } catch (e: any) {
        console.error('[loadDemoDataAction] Catastrophic Failure:', e.message)
        return { error: `Catastrophic Failure: ${e.message}` }
    }
}

export async function clearAllDataAction() {
    const supabase = await createClient()
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) return { error: 'Unauthenticated' }

    try {
        const tables = [
            'production_tasks', 'routings', 'work_centers', 'inventory_batches', 'locations',
            'so_items', 'sales_orders', 'po_items', 'purchase_orders', 'production_orders', 
            'bom_items', 'items', 'customers', 'suppliers'
        ]
        for (const tbl of tables) {
            await supabase.from(tbl).delete().eq('user_id', user.id)
        }
        revalidatePath('/')
        return { success: true }
    } catch (e: any) {
        return { error: e.message }
    }
}
