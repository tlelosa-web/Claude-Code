import { getItems } from '@/lib/actions/items'
import { getSuppliers } from '@/lib/actions/suppliers'
import { getInventoryBatches, getLocations } from '@/lib/actions/inventory'
import TopBar from '@/components/layout/TopBar'
import InventoryClient from './InventoryClient'

export default async function InventoryPage() {
    const [rawMaterials, suppliers, batches, locations] = await Promise.all([
        getItems('Material'), 
        getSuppliers(),
        getInventoryBatches(),
        getLocations()
    ])
    return (
        <>
            <TopBar pageTitle="Inventory (Materials)" />
            <InventoryClient 
                rawMaterials={rawMaterials} 
                suppliers={suppliers} 
                batches={batches} 
                locations={locations} 
            />
        </>
    )
}
