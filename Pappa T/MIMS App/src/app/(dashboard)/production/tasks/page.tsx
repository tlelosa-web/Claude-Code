import TopBar from '@/components/layout/TopBar'
import { getProductionTasks } from '@/lib/actions/production'
import ProductionTasksClient from './ProductionTasksClient'

export default async function ProductionTasksPage() {
    const tasks = await getProductionTasks()
    return (
        <>
            <TopBar pageTitle="Shop Floor Tasks" />
            <ProductionTasksClient tasks={tasks} />
        </>
    )
}
