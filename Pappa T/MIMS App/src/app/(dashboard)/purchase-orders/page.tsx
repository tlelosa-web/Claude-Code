import { getPurchaseOrders } from '@/lib/actions/purchase-orders'
import { getSuppliers } from '@/lib/actions/suppliers'
import { getItems } from '@/lib/actions/items'
import { getLocations } from '@/lib/actions/inventory'
import TopBar from '@/components/layout/TopBar'
import PurchaseOrdersClient from './PurchaseOrdersClient'

export default async function PurchaseOrdersPage() {
    const [orders, suppliers, rawMaterials, locations] = await Promise.all([
        getPurchaseOrders(), 
        getSuppliers(), 
        getItems('Material'),
        getLocations()
    ])
    return (
        <>
            <TopBar pageTitle="Purchase Orders" />
            <PurchaseOrdersClient orders={orders} suppliers={suppliers} rawMaterials={rawMaterials} locations={locations} />
        </>
    )
}
