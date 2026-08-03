import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'
import Sidebar from '@/components/layout/Sidebar'

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
    const supabase = await createClient()
    const { data: { user } } = await supabase.auth.getUser()

    if (!user) redirect('/login')

    return (
        <div className="flex min-h-screen">
            <Sidebar />
            <main className="ml-64 flex-1 p-8 min-w-0">
                {children}
            </main>
        </div>
    )
}
