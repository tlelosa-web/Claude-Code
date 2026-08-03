"""career-engine CLI — wires the 5 pipeline stages together (Build Queue
step 51, Phase 7). Mirrors ai-outreach-agency/src/main.py's argparse +
dispatch-dict shape, adapted to this project's own pipeline stages.

No auto-submission exists past `run_review_gate` — the human approval gate
is the terminal stage of this build (CLAUDE.md Hard Rule #1)."""

import argparse
import json
import sys
from pathlib import Path

from src.config import load_settings
from src.doc_gen.pipeline import run_doc_gen
from src.matching.pipeline import run_matching
from src.profile.db import get_profile, init_db as init_profile_db, upsert_profile
from src.profile.schema import CandidateProfile
from src.review.cli import run_review_gate
from src.vacancy_search.apify_client import fetch_vacancies
from src.vacancy_search.db import (
    get_by_id,
    get_by_status,
    init_db as init_vacancy_db,
    insert_vacancy,
)
from src.vacancy_search.schema import VALID_STATUSES


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="career-engine",
        description="TebelloReborn Career Engine — job application pipeline CLI",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_import = subparsers.add_parser(
        "import-profile", help="Load/update the candidate profile from a JSON file"
    )
    p_import.add_argument("--file", required=True, help="Path to profile_seed.json")

    p_fetch = subparsers.add_parser(
        "fetch-vacancies", help="Scrape vacancies from Indeed + LinkedIn via Apify"
    )
    p_fetch.add_argument(
        "--limit", type=int, default=25, help="Max vacancies to fetch (default: 25)"
    )

    p_list = subparsers.add_parser(
        "list", help="List vacancies and their current status"
    )
    p_list.add_argument(
        "--status", default=None, help="Filter by status (default: all)"
    )

    p_run = subparsers.add_parser(
        "run", help="Score + generate assets and review one vacancy"
    )
    p_run.add_argument(
        "--vacancy-id", type=int, required=True, help="Vacancy ID to process"
    )

    p_run_all = subparsers.add_parser(
        "run-all", help="Run the pipeline for every vacancy with a given status"
    )
    p_run_all.add_argument(
        "--status", default="new", help="Status to filter by (default: new)"
    )

    return parser


def cmd_import_profile(args, settings) -> None:
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: file not found: {file_path}")
        sys.exit(1)

    data = json.loads(file_path.read_text(encoding="utf-8"))
    profile = CandidateProfile.from_dict(data)

    conn = init_profile_db(Path(settings.DB_PATH))
    try:
        upsert_profile(conn, profile)
    finally:
        conn.close()

    print(f"Profile imported: {profile.name}")


def cmd_fetch_vacancies(args, settings) -> None:
    vacancies = fetch_vacancies(args.limit)

    conn = init_vacancy_db(Path(settings.DB_PATH))
    try:
        inserted = 0
        for vacancy in vacancies:
            if insert_vacancy(conn, vacancy) is not None:
                inserted += 1
    finally:
        conn.close()

    print(f"Fetched {len(vacancies)} vacancies, {inserted} new.")


def cmd_list(args, settings) -> None:
    conn = init_vacancy_db(Path(settings.DB_PATH))
    try:
        if args.status:
            vacancies = list(get_by_status(conn, args.status))
        else:
            vacancies = []
            for status in VALID_STATUSES:
                vacancies.extend(get_by_status(conn, status))
    finally:
        conn.close()

    if not vacancies:
        print("No vacancies found.")
        return

    print(f"{'ID':<6} {'Company':<30} {'Title':<30} {'Status':<12} {'Score':<6}")
    print("-" * 90)
    for v in vacancies:
        score = v.score if v.score is not None else "-"
        print(f"{v.id:<6} {v.company:<30} {v.title:<30} {v.status:<12} {score!s:<6}")

    print(f"\nTotal: {len(vacancies)} vacancies")


def _run_pipeline_for_vacancy(vacancy, profile, db_path) -> None:
    """Score → generate → review a single vacancy. Passes the exact
    generated cv_text/cover_letter_text (set on the Vacancy by
    run_doc_gen) through to the human review gate — never a re-generated
    copy, never nothing (see CLAUDE.md Hard Rule #1).

    run_doc_gen only transitions status to 'asset_ready' if both the CV
    and cover letter generate successfully (see its own docstring) — a
    throttled/errored generation (e.g. a headless `claude -p` timeout)
    leaves the vacancy at 'scored' with cv_text/cover_letter_text still
    None. Presenting that to the review gate would show a human a blank
    CV/cover letter to approve — skip the gate entirely and report the
    failure instead (real bug found 2026-08-01: a CV generation timeout
    reached the review prompt with 'CV: None' / 'Cover Letter: None')."""
    scored_vacancy = run_matching(vacancy, profile, db_path=db_path)
    asset_ready_vacancy = run_doc_gen(profile, scored_vacancy, db_path=db_path)

    if asset_ready_vacancy.status != "asset_ready":
        print(
            f"  Skipping vacancy {asset_ready_vacancy.id} "
            f"({asset_ready_vacancy.company} — {asset_ready_vacancy.title}): "
            f"document generation did not complete (status still "
            f"'{asset_ready_vacancy.status}'). Check generation_log for "
            "the error; re-run once resolved."
        )
        return

    run_review_gate(
        asset_ready_vacancy,
        asset_ready_vacancy.cv_text,
        asset_ready_vacancy.cover_letter_text,
        db_path=db_path,
    )


def cmd_run(args, settings) -> None:
    db_path = Path(settings.DB_PATH)

    conn = init_vacancy_db(db_path)
    try:
        vacancy = get_by_id(conn, args.vacancy_id)
    finally:
        conn.close()

    if vacancy is None:
        print(f"Error: no vacancy found with ID {args.vacancy_id}")
        sys.exit(1)

    profile_conn = init_profile_db(db_path)
    try:
        profile = get_profile(profile_conn)
    finally:
        profile_conn.close()

    _run_pipeline_for_vacancy(vacancy, profile, db_path)


def cmd_run_all(args, settings) -> None:
    db_path = Path(settings.DB_PATH)
    status = args.status

    conn = init_vacancy_db(db_path)
    try:
        vacancies = get_by_status(conn, status)
    finally:
        conn.close()

    if not vacancies:
        print(f"No vacancies with status '{status}'.")
        return

    profile_conn = init_profile_db(db_path)
    try:
        profile = get_profile(profile_conn)
    finally:
        profile_conn.close()

    print(
        f"Found {len(vacancies)} vacancies with status '{status}'. "
        "Processing one at a time.\n"
    )

    for vacancy in vacancies:
        try:
            _run_pipeline_for_vacancy(vacancy, profile, db_path)
        except SystemExit:
            print("\nQuit requested. Stopping pipeline.")
            break


def main(argv=None) -> None:
    settings = load_settings()
    parser = build_parser()
    args = parser.parse_args(argv)

    dispatch = {
        "import-profile": cmd_import_profile,
        "fetch-vacancies": cmd_fetch_vacancies,
        "list": cmd_list,
        "run": cmd_run,
        "run-all": cmd_run_all,
    }

    dispatch[args.command](args, settings)


if __name__ == "__main__":
    main()
