import { getSalesOrders } from '@/lib/actions/sales-orders'
import { getLocations, getInventoryBatches } from '@/lib/actions/inventory'
import TopBar from '@/components/layout/TopBar'
import DispatchClient from './DispatchClient'

export default async function DispatchPage() {
    const [orders, locations, batches] = await Promise.all([
        getSalesOrders(),
        getLocations(),
        getInventoryBatches()
    ])
    const readyOrders = orders.filter((o: any) => o.status === 'Ready for Dispatch')
    return (
        <>
            <TopBar pageTitle="Dispatch" />
            <DispatchClient orders={readyOrders} locations={locations} batches={batches} />
        </>
    )
}
