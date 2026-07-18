'use server'

import { createClient } from '@/lib/supabase/server'
import { revalidatePath } from 'next/cache'

export async function getProductionOrders() {
    const supabase = await createClient()
    const { data } = await supabase
        .from('production_orders')
        .select('*, item:items(id,code,description, bom_items!bom_items_parent_item_id_fkey(*, component:items!bom_items_component_item_id_fkey(id,code,avg_cost))), production_tasks(*, work_center:work_centers(name))')
        .order('created_at', { ascending: false })
    return data ?? []
}

export async function createProductionOrder(formData: FormData) {
    const supabase = await createClient()
    
    // 1. Auth Verification
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) throw new Error('Unauthenticated')

    const itemId = formData.get('item_id') as string
    const qty = parseFloat(formData.get('quantity') as string)
    const dueDate = formData.get('due_date') as string

    try {
        const { count } = await supabase.from('production_orders').select('*', { count: 'exact', head: true }).eq('user_id', user.id)
        const orderNumber = `WO-${String((count ?? 0) + 1001).padStart(4, '0')}`

        const { data: wo, error: woError } = await supabase.from('production_orders').insert({
            user_id: user.id,
            order_number: orderNumber,
            item_id: itemId,
            quantity: qty,
            status: 'Pending',
            due_date: dueDate,
        }).select('id').single()

        if (woError) throw woError
        if (!wo) throw new Error('Production order creation failed')

        // 2. Generate tasks and increment demand
        await (supabase.rpc as any)('create_production_tasks', { 
            p_production_order_id: wo.id, 
            p_user_id: user.id 
        })
        
        // 3. Increment demand for components
        const { data: items } = await supabase.from('bom_items').select('component_item_id, qty_per_unit').eq('parent_item_id', itemId)
        for (const b of items ?? []) {
            const { error: dError } = await (supabase.rpc as any)('modify_item_stats', {
                p_item_id: b.component_item_id,
                p_demand_delta: b.qty_per_unit * qty,
                p_order_delta: 0
            })
            if (dError) console.error('[createProductionOrder] Demand update failed:', dError)
        }

        revalidatePath('/production')
        revalidatePath('/inventory')
        revalidatePath('/')
        return { success: true }
    } catch (e: any) {
        console.error('[createProductionOrder] Failure:', e.message)
        return { error: e.message }
    }
}

export async function startProductionOrder(woId: string) {
    const supabase = await createClient()
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) throw new Error('Unauthenticated')

    // Simple status update for now. 
    // Actual material deduction should happen either at start or per task.
    // Typical MRP behavior: materials are "Committed" then "Consumed".
    
    await supabase.from('production_orders').update({ status: 'In Progress' }).eq('id', woId).eq('user_id', user.id)
    await supabase.from('production_tasks').update({ status: 'In Progress' }).eq('production_order_id', woId).eq('sequence_order', 1).eq('user_id', user.id)

    revalidatePath('/production')
}

export async function updateProductionTaskStatus(taskId: string, status: string, actualMins: number = 0) {
    const supabase = await createClient()
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) throw new Error('Unauthenticated')

    if (status === 'Completed') {
        await (supabase.rpc as any)('complete_production_task', {
            p_task_id: taskId,
            p_actual_mins: actualMins,
            p_user_id: user.id
        })
    } else {
        // On first start, set started_at
        if (status === 'In Progress') {
            await supabase.from('production_tasks')
                .update({ status, started_at: new Date().toISOString() })
                .eq('id', taskId)
                .eq('user_id', user.id)
                .is('started_at', null)
        } else {
            await supabase.from('production_tasks').update({ status }).eq('id', taskId).eq('user_id', user.id)
        }
    }

    revalidatePath('/production')
}

export async function getProductionTasks() {
    const supabase = await createClient()
    const { data, error } = await supabase
        .from('production_tasks')
        .select('*, work_center:work_centers(name, hourly_rate), order:production_orders(id, order_number, item:items(id, code, description), quantity, due_date)')
        .order('started_at', { ascending: true })
    if (error) {
        console.error('[getProductionTasks] Error:', error.message)
        return []
    }
    return data ?? []
}
export async function completeProductionOrder(woId: string, locationId: string, batchNumber: string) {
    const supabase = await createClient()
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) throw new Error('Unauthenticated')

    const { data: wo } = await supabase
        .from('production_orders').select('item_id, quantity').eq('id', woId).single()
    if (!wo) throw new Error('Order not found')

    // 1. Calculate final cost (Material recursive cost + Labor from tasks)
    const materialCost = await (supabase.rpc as any)('get_bom_cost', { p_item_id: wo.item_id })
    const { data: tasks } = await supabase.from('production_tasks').select('labor_cost, work_center:work_centers(overhead_pct)').eq('production_order_id', woId)
    const laborCostTotal = (tasks ?? []).reduce((s, t) => s + (t.labor_cost ?? 0), 0)
    const unitLaborCost = laborCostTotal / wo.quantity
    const baseUnitCost = (materialCost?.data ?? 0) + unitLaborCost
    const overheadAvg = (() => {
        const arr = (tasks ?? []).map((t: any) => t.work_center?.overhead_pct ?? 0)
        if (arr.length === 0) return 0
        return arr.reduce((a, b) => a + b, 0) / arr.length
    })()
    const finalUnitCost = baseUnitCost * (1 + (overheadAvg ?? 0) / 100)

    // 2. Add Finished Good to inventory
    await (supabase.rpc as any)('adjust_inventory', {
        p_item_id: wo.item_id,
        p_location_id: locationId,
        p_batch_number: batchNumber,
        p_qty: wo.quantity,
        p_cost: finalUnitCost,
        p_user_id: user.id
    })

    // 3. Mark order as completed
    await supabase.from('production_orders').update({ status: 'Completed' }).eq('id', woId).eq('user_id', user.id)

    // 4. Decrement demand for components (Consumption logic)
    revalidatePath('/')
}

export async function cancelProductionOrder(woId: string) {
    const supabase = await createClient()
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) throw new Error('Unauthenticated')

    const { data: wo } = await supabase.from('production_orders').select('item_id, quantity, status').eq('id', woId).single()
    if (!wo || wo.status === 'Completed' || wo.status === 'Cancelled') return

    // Decrement demand for components
    const { data: bom } = await supabase.from('items').select('bom_items!bom_items_parent_item_id_fkey(component_item_id, qty_per_unit)').eq('id', wo.item_id)
    for (const b of (bom as any)?.[0]?.bom_items ?? []) {
        const { data: comp } = await supabase.from('items').select('demand').eq('id', b.component_item_id).single()
        await supabase.from('items').update({ 
            demand: Math.max(0, (comp?.demand ?? 0) - (b.qty_per_unit * wo.quantity)) 
        }).eq('id', b.component_item_id)
    }

    await supabase.from('production_orders').update({ status: 'Cancelled' }).eq('id', woId).eq('user_id', user.id)
    revalidatePath('/production')
}
