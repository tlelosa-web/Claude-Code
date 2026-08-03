'use server'

import { createClient } from '@/lib/supabase/server'
import { revalidatePath } from 'next/cache'

export async function getPurchaseOrders() {
    const supabase = await createClient()
    const { data } = await supabase
        .from('purchase_orders')
        .select('*, supplier:suppliers(id,name), po_items(*, item:items(id,code,description))')
        .order('created_at', { ascending: false })
    return data ?? []
}

export async function createPurchaseOrder(formData: FormData) {
    const supabase = await createClient()
    
    // 1. Auth Verification
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) throw new Error('Unauthenticated')

    const itemsJson = formData.get('items') as string
    const items: { item_id: string; quantity: number; unit_cost: number }[] = JSON.parse(itemsJson)
    const total = items.reduce((s, i) => s + i.quantity * i.unit_cost, 0)

    try {
        const { count } = await supabase.from('purchase_orders').select('*', { count: 'exact', head: true }).eq('user_id', user.id)
        const orderNumber = `PO-${String((count ?? 0) + 1001).padStart(4, '0')}`

        const { data: po, error: poError } = await supabase.from('purchase_orders').insert({
            user_id: user.id,
            order_number: orderNumber,
            supplier_id: formData.get('supplier_id') as string,
            delivery_date: formData.get('delivery_date') as string,
            status: 'Ordered',
            total,
        }).select('id').single()

        if (poError) throw poError
        if (!po) throw new Error('Purchase order creation failed')

        await supabase.from('po_items').insert(
            items.map(i => ({ ...i, purchase_order_id: po.id, user_id: user.id }))
        )

        // 2. Increment on_order for each Item
        for (const item of items) {
            const { error: dError } = await (supabase.rpc as any)('modify_item_stats', {
                p_item_id: item.item_id,
                p_demand_delta: 0,
                p_order_delta: item.quantity
            })
            if (dError) console.error('[createPurchaseOrder] On Order update failed:', dError)
        }

        revalidatePath('/purchase-orders')
        revalidatePath('/inventory')
        revalidatePath('/')
        return { success: true }
    } catch (e: any) {
        console.error('[createPurchaseOrder] Failure:', e.message)
        return { error: e.message }
    }
}

export async function receivePurchaseOrder(poId: string, locationId: string) {
    const supabase = await createClient()
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) throw new Error('Unauthenticated')

    const { data: items } = await supabase
        .from('po_items')
        .select('item_id, quantity, unit_cost')
        .eq('purchase_order_id', poId)

    if (items) {
        for (const item of items) {
            // Use unified adjust_inventory RPC
            await (supabase.rpc as any)('adjust_inventory', {
                p_item_id: item.item_id,
                p_location_id: locationId,
                p_batch_number: `PO-${poId.slice(0,8)}`, // Use PO ID as batch prefix
                p_qty: item.quantity,
                p_cost: item.unit_cost,
                p_user_id: user.id,
            })
            
            // Decrement on_order
            const { data: existing } = await supabase.from('items').select('on_order').eq('id', item.item_id).single()
            await supabase.from('items').update({ 
                on_order: Math.max(0, (existing?.on_order ?? 0) - item.quantity) 
            }).eq('id', item.item_id)
        }
    }

    revalidatePath('/')
}

export async function cancelPurchaseOrder(poId: string) {
    const supabase = await createClient()
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) throw new Error('Unauthenticated')

    const { data: items } = await supabase.from('po_items').select('item_id, quantity').eq('purchase_order_id', poId)
    for (const i of items ?? []) {
        const { data: it } = await supabase.from('items').select('on_order').eq('id', i.item_id).single()
        await supabase.from('items').update({ on_order: Math.max(0, (it?.on_order ?? 0) - i.quantity) }).eq('id', i.item_id)
    }

    await supabase.from('purchase_orders').update({ status: 'Cancelled' }).eq('id', poId).eq('user_id', user.id)
    revalidatePath('/purchase-orders')
}
