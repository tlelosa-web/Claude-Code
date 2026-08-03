import { getSalesOrders } from '@/lib/actions/sales-orders'
import { getCustomers } from '@/lib/actions/customers'
import { getItems } from '@/lib/actions/items'
import TopBar from '@/components/layout/TopBar'
import SalesOrdersClient from './SalesOrdersClient'

export default async function SalesOrdersPage() {
    const [orders, customers, finishedGoods] = await Promise.all([
        getSalesOrders(), getCustomers(), getItems('Product')
    ])
    return (
        <>
            <TopBar pageTitle="Sales Orders" />
            <SalesOrdersClient orders={orders} customers={customers} finishedGoods={finishedGoods} />
        </>
    )
}
