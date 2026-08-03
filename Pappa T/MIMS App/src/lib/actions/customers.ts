'use server'

import { createClient } from '@/lib/supabase/server'
import { revalidatePath } from 'next/cache'

export async function getCustomers() {
    const supabase = await createClient()
    const { data } = await supabase.from('customers').select('*').order('name')
    return data ?? []
}

export async function upsertCustomer(formData: FormData) {
    const supabase = await createClient()
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) throw new Error('Unauthenticated')

    const id = formData.get('id') as string
    const payload = {
        user_id: user.id,
        name: formData.get('name') as string,
        contact: formData.get('contact') as string,
        email: formData.get('email') as string,
        city: formData.get('city') as string,
    }

    if (id) {
        await supabase.from('customers').update(payload).eq('id', id).eq('user_id', user.id)
    } else {
        await supabase.from('customers').insert(payload)
    }
    revalidatePath('/customers')
}

export async function deleteCustomer(id: string) {
    const supabase = await createClient()
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) throw new Error('Unauthenticated')
    await supabase.from('customers').delete().eq('id', id).eq('user_id', user.id)
    revalidatePath('/customers')
}
