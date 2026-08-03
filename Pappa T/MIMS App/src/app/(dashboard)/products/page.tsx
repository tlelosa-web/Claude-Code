import { getItems } from '@/lib/actions/items'
import { getInventoryBatches } from '@/lib/actions/inventory'
import TopBar from '@/components/layout/TopBar'
import ProductsClient from './ProductsClient'

export default async function ProductsPage() {
    const [allProducts, rawMaterials, batches] = await Promise.all([
        getItems(),
        getItems('Material'),
        getInventoryBatches()
    ])
    const finishedGoods = allProducts.filter(i => i.type !== 'Material')
    
    return (
        <>
            <TopBar pageTitle="Products & Assemblies" />
            <ProductsClient finishedGoods={finishedGoods} rawMaterials={rawMaterials} batches={batches} />
        </>
    )
}
