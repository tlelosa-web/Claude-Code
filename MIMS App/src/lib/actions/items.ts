'use server'

import { createClient } from '@/lib/supabase/server'
import { revalidatePath } from 'next/cache'

export async function getItems(type?: 'Material' | 'Sub-Assembly' | 'Product') {
    const supabase = await createClient()
    
    // 1. Auth check
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) return []

    try {
        let query = supabase.from('items').select('*, supplier:suppliers(id,name), bom_items!bom_items_parent_item_id_fkey(*, component:items!bom_items_component_item_id_fkey(id,code,description,avg_cost))')
        
        if (type) query = query.eq('type', type)
        
        const { data, error } = await query.order('code')
        
        // 2. Error check
        if (error) {
            console.error('[getItems] Supabase Error:', error.message)
            return []
        }

        return data ?? []
    } catch (e: any) {
        console.error('[getItems] Catastrophic Failure:', e.message)
        return []
    }
}

export async function upsertItem(formData: FormData) {
    const supabase = await createClient()
    
    // 1. Auth Verification
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) throw new Error('Unauthenticated')

    const id = formData.get('id') as string
    const payload = {
        user_id: user.id,
        code: formData.get('code') as string,
        description: formData.get('description') as string,
        category: (formData.get('category') as string) || 'Default',
        type: (formData.get('type') as any) || 'Product',
        uom: (formData.get('uom') as string) || 'pcs',
        min_stock: parseFloat(formData.get('min_stock') as string) || 0,
        lead_days: parseInt(formData.get('lead_days') as string) || 0,
        avg_cost: parseFloat(formData.get('avg_cost') as string) || 0,
        sales_price: parseFloat(formData.get('sales_price') as string) || 0,
    }

    try {
        let itemId = id
        if (id) {
            const { error: upError } = await supabase.from('items').update(payload).eq('id', id).eq('user_id', user.id)
            if (upError) throw upError
            
            // Clear existing BOM
            await supabase.from('bom_items').delete().eq('parent_item_id', id).eq('user_id', user.id)
        } else {
            const { data, error: inError } = await supabase.from('items').insert(payload).select('id').single()
            if (inError) throw inError
            if (!data) throw new Error('Insert returned no data')
            itemId = data.id
        }

        // 3. Insert BOM rows
        const bomJson = formData.get('bom') as string
        if (bomJson && itemId) {
            const bom: { component_item_id: string; qty_per_unit: number }[] = JSON.parse(bomJson)
            if (bom.length > 0) {
                const { error: bomError } = await supabase.from('bom_items').insert(
                    bom.map(b => ({ ...b, parent_item_id: itemId, user_id: user.id }))
                )
                if (bomError) throw bomError
            }
        }

        revalidatePath('/products')
        revalidatePath('/inventory')
        revalidatePath('/')
        return { success: true }
    } catch (e: any) {
        console.error('[upsertItem] Failure:', e.message)
        return { error: e.message }
    }
}

export async function deleteItem(id: string) {
    const supabase = await createClient()
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) throw new Error('Unauthenticated')

    try {
        const { error } = await supabase.from('items').delete().eq('id', id).eq('user_id', user.id)
        if (error) throw error
        
        revalidatePath('/products')
        revalidatePath('/inventory')
        revalidatePath('/')
        return { success: true }
    } catch (e: any) {
        console.error('[deleteItem] Failure:', e.message)
        return { error: e.message }
    }
}

export async function getBOMCost(itemId: string) {
    const supabase = await createClient()
    try {
        const { data, error } = await (supabase.rpc as any)('get_bom_cost', { p_item_id: itemId })
        if (error) throw error
        return data ?? 0
    } catch (e: any) {
        console.error('[getBOMCost] Failure:', e.message)
        return 0
    }
}

export async function getReorderSuggestions() {
    const supabase = await createClient()
    // 1. Auth check
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) return []

    try {
        const { data, error } = await supabase.from('items').select('id, code, description, stock, on_order, min_stock, lead_days')
        if (error) {
            console.error('[getReorderSuggestions] Supabase Error:', error.message)
            return []
        }
        const items = data ?? []
        return items.filter(i => (Number(i.stock ?? 0) + Number(i.on_order ?? 0)) < Number(i.min_stock ?? 0))
    } catch (e: any) {
        console.error('[getReorderSuggestions] Catastrophic Failure:', e.message)
        return []
    }
}
