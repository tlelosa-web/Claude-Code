'use server'

import { createClient } from '@/lib/supabase/server'
import { revalidatePath } from 'next/cache'

export async function getSalesOrders() {
    const supabase = await createClient()
    const { data } = await supabase
        .from('sales_orders')
        .select('*, customer:customers(id,name), so_items(*, item:items(id,code,description,sales_price))')
        .order('created_at', { ascending: false })
    return data ?? []
}

export async function createSalesOrder(formData: FormData) {
    const supabase = await createClient()
    
    // 1. Auth Verification
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) throw new Error('Unauthenticated')

    const itemsJson = formData.get('items') as string
    const items: { item_id: string; quantity: number; unit_price: number }[] = JSON.parse(itemsJson)

    try {
        const { count } = await supabase.from('sales_orders').select('*', { count: 'exact', head: true }).eq('user_id', user.id)
        const orderNumber = `SO-${String((count ?? 0) + 1001).padStart(4, '0')}`

        const { data: so, error: soError } = await supabase.from('sales_orders').insert({
            user_id: user.id,
            order_number: orderNumber,
            customer_id: formData.get('customer_id') as string,
            delivery_date: formData.get('delivery_date') as string,
            status: 'Confirmed',
        }).select('id').single()

        if (soError) throw soError
        if (!so) throw new Error('Sales order creation failed')

        await supabase.from('so_items').insert(
            items.map(i => ({ ...i, sales_order_id: so.id, user_id: user.id }))
        )
        
        // 2. Increment Item demand (Committed)
        for (const item of items) {
            const { error: dError } = await (supabase.rpc as any)('modify_item_stats', {
                p_item_id: item.item_id,
                p_demand_delta: item.quantity,
                p_order_delta: 0
            })
            if (dError) console.error('[createSalesOrder] Demand update failed:', dError)
        }

        revalidatePath('/sales-orders')
        revalidatePath('/products')
        revalidatePath('/')
        return { success: true }
    } catch (e: any) {
        console.error('[createSalesOrder] Failure:', e.message)
        return { error: e.message }
    }
}

export async function dispatchSalesOrder(soId: string, locationId: string, batchId: string) {
    const supabase = await createClient()
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) throw new Error('Unauthenticated')

    const { data: items } = await supabase
        .from('so_items')
        .select('item_id, quantity')
        .eq('sales_order_id', soId)

    for (const item of items ?? []) {
        // Use adjust_inventory with negative quantity for dispatch
        await (supabase.rpc as any)('adjust_inventory', {
            p_item_id: item.item_id,
            p_location_id: locationId,
            p_batch_number: batchId, // Should ideally select a batch with enough stock
            p_qty: -item.quantity,
            p_cost: 0, // Cost is fixed on the batch already
            p_user_id: user.id,
        })
        
        // Decrement demand
        const { data: existing } = await supabase.from('items').select('demand').eq('id', item.item_id).single()
        await supabase.from('items').update({ 
            demand: Math.max(0, (existing?.demand ?? 0) - item.quantity) 
        }).eq('id', item.item_id)
    }

    await supabase.from('sales_orders').update({ status: 'Dispatched' }).eq('id', soId).eq('user_id', user.id)
    revalidatePath('/dispatch')
    revalidatePath('/sales-orders')
    revalidatePath('/')
}

export async function checkStockAndReadySO(soId: string) {
    const supabase = await createClient()
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) throw new Error('Unauthenticated')

    // Simple check: do we have enough stock across all batches for each item?
    // In a real app, this would be more complex (batch reservation).
    await supabase.from('sales_orders').update({ status: 'Ready for Dispatch' }).eq('id', soId).eq('user_id', user.id)
    revalidatePath('/sales-orders')
    revalidatePath('/dispatch')
}

export async function cancelSalesOrder(soId: string) {
    const supabase = await createClient()
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) throw new Error('Unauthenticated')

    const { data: items } = await supabase.from('so_items').select('item_id, quantity').eq('sales_order_id', soId)
    for (const i of items ?? []) {
        const { data: it } = await supabase.from('items').select('demand').eq('id', i.item_id).single()
        await supabase.from('items').update({ demand: Math.max(0, (it?.demand ?? 0) - i.quantity) }).eq('id', i.item_id)
    }

    await supabase.from('sales_orders').update({ status: 'Cancelled' }).eq('id', soId).eq('user_id', user.id)
    revalidatePath('/sales-orders')
}
