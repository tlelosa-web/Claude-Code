import { getCustomers } from '@/lib/actions/customers'
import TopBar from '@/components/layout/TopBar'
import CustomersClient from './CustomersClient'

export default async function CustomersPage() {
    const customers = await getCustomers()
    return (
        <>
            <TopBar pageTitle="Customers" />
            <CustomersClient customers={customers} />
        </>
    )
}
