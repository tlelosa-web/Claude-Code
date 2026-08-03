from src.profile.schema import CandidateProfile
from src.vacancy_search.schema import Vacancy


def build_match_prompt(profile: CandidateProfile, vacancy: Vacancy) -> str:
    """Pure function, no network — builds the scoring prompt for the local
    Ollama matcher from a candidate profile and one vacancy."""
    lanes = sorted(profile.target_titles, key=lambda lane: (not lane.primary, -lane.weight))
    lane_lines = "\n".join(
        f"- {lane.title} ({'primary' if lane.primary else 'secondary'} lane, weight {lane.weight})"
        for lane in lanes
    )

    return (
        "You are scoring how well a candidate matches a job vacancy.\n\n"
        f"Candidate: {profile.name}\n"
        f"Region: {profile.region}\n"
        f"Target title lanes (weighted; match against the primary lane first, "
        f"the secondary lane matters less):\n{lane_lines}\n"
        f"Skills: {', '.join(profile.skills)}\n\n"
        f"Vacancy: {vacancy.title} at {vacancy.company}\n"
        f"Description: {vacancy.description}\n\n"
        "Score this vacancy from 0-100 on fit. Respond with JSON only: "
        '{"score": <int 0-100>, "strengths": [<string>, ...], '
        '"weaknesses": [<string>, ...], "recommendation": "<string>"}'
    )
