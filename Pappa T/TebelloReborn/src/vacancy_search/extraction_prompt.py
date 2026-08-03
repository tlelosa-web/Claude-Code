from src.doc_gen.runner import wrap_untrusted_text


def build_extraction_prompt(raw_page_text: str, platform: str) -> str:
    """Pure function, no network, no DB — builds the JSON-schema-shaped
    extraction prompt for the local Ollama extractor from one raw crawled
    job-detail page's text content.

    raw_page_text is untrusted, scraped job-posting text — the same sink
    shape as vacancy.description in doc_gen's cv_generator.py/
    cover_letter_generator.py — so it is wrapped with the same
    wrap_untrusted_text() delimiters as defense in depth before reaching
    the LLM prompt."""
    return (
        f"You are extracting structured vacancy fields from a {platform} "
        "job-detail page's raw text. The page describes exactly ONE job "
        "vacancy — extract fields for that one vacancy only, even if the "
        "text mentions other roles or companies in passing.\n\n"
        f"Raw page text:\n{wrap_untrusted_text(raw_page_text)}\n\n"
        "Respond with JSON only, using exactly these keys: "
        '{"company": "<string>", "title": "<string>", '
        '"description": "<string>", "url": "<string>", '
        '"salary": "<string or null>", "deadline": "<string or null>"}. '
        "company, title, and url are required and must not be empty "
        "strings — if you cannot determine one confidently, do not guess; "
        "leave salary/deadline null when not stated."
    )
