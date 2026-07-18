'use server'

import { createClient } from '@/lib/supabase/server'
import { revalidatePath } from 'next/cache'

export async function getSuppliers() {
    const supabase = await createClient()
    const { data } = await supabase.from('suppliers').select('*').order('name')
    return data ?? []
}

export async function upsertSupplier(formData: FormData) {
    const supabase = await createClient()
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) throw new Error('Unauthenticated')

    const id = formData.get('id') as string
    const payload = {
        user_id: user.id,
        name: formData.get('name') as string,
        contact: formData.get('contact') as string,
        email: formData.get('email') as string,
        phone: formData.get('phone') as string,
    }

    if (id) {
        await supabase.from('suppliers').update(payload).eq('id', id).eq('user_id', user.id)
    } else {
        await supabase.from('suppliers').insert(payload)
    }
    revalidatePath('/suppliers')
}

export async function deleteSupplier(id: string) {
    const supabase = await createClient()
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) throw new Error('Unauthenticated')
    await supabase.from('suppliers').delete().eq('id', id).eq('user_id', user.id)
    revalidatePath('/suppliers')
}
