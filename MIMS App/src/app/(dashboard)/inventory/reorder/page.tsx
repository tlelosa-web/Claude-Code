import TopBar from '@/components/layout/TopBar'
import { getReorderSuggestions } from '@/lib/actions/items'
import ReorderSuggestionsClient from './ReorderSuggestionsClient'

export default async function ReorderPage() {
    const suggestions = await getReorderSuggestions()
    return (
        <>
            <TopBar pageTitle="Reorder Suggestions" />
            <ReorderSuggestionsClient suggestions={suggestions} />
        </>
    )
}
