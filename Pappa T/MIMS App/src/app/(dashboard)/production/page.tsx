import { getProductionOrders } from '@/lib/actions/production'
import { getItems } from '@/lib/actions/items'
import { getLocations } from '@/lib/actions/inventory'
import TopBar from '@/components/layout/TopBar'
import ProductionClient from './ProductionClient'

export default async function ProductionPage() {
    const [orders, allItems, locations] = await Promise.all([
        getProductionOrders(), 
        getItems(),
        getLocations()
    ])
    const finishedGoods = allItems.filter(i => i.type !== 'Material')
    
    return (
        <>
            <TopBar pageTitle="Production Orders" />
            <ProductionClient orders={orders} finishedGoods={finishedGoods} locations={locations} />
        </>
    )
}
