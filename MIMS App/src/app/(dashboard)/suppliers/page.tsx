import { getSuppliers } from '@/lib/actions/suppliers'
import TopBar from '@/components/layout/TopBar'
import SuppliersClient from './SuppliersClient'

export default async function SuppliersPage() {
    const suppliers = await getSuppliers()
    return (
        <>
            <TopBar pageTitle="Suppliers" />
            <SuppliersClient suppliers={suppliers} />
        </>
    )
}
