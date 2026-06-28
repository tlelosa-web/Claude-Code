class ApifyClient:
    # TODO: replace with real Apify Actor call
    def scrape_company(self, website: str) -> dict:
        return {
            "url": website,
            "title": "Example Engineering Co.",
            "about": "A leading heavy engineering and fabrication firm based in Gauteng.",
            "services": ["Steel fabrication", "Plant maintenance", "Mechanical installations"],
            "recent_news": "Awarded new contract for mine conveyor system upgrade.",
        }
