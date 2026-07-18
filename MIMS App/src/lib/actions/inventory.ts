'use server'

import { createClient } from '@/lib/supabase/server'

export async function getLocations() {
    const supabase = await createClient()
    const { data, error } = await supabase.from('locations').select('*').order('name')
    if (error) {
        console.error('[getLocations] Error:', error.message)
        return []
    }
    return data ?? []
}

export async function getInventoryBatches(itemId?: string) {
    const supabase = await createClient()
    let query = supabase.from('inventory_batches').select('*, location:locations(name), item:items(code)')
    if (itemId) query = query.eq('item_id', itemId)
    
    const { data, error } = await query.order('created_at', { ascending: false })
    if (error) {
        console.error('[getInventoryBatches] Error:', error.message)
        return []
    }
    return data ?? []
}
