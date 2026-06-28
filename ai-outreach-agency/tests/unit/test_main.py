import csv
import sqlite3
from pathlib import Path

import pytest

from src.main import main, build_parser
from src.lead_import.db import init_db, insert_lead, get_all_leads
from src.lead_import.schema import Lead


def _write_csv(path: Path, headers: list, rows: list):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)


def _make_lead(**overrides) -> Lead:
    defaults = dict(
        company_name="Acme Engineering",
        contact_name="John Smith",
        contact_title="Operations Manager",
        email="john@acme.co.za",
        source="apollo",
    )
    defaults.update(overrides)
    return Lead(**defaults)


class TestArgParsing:
    def test_import_requires_csv(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["import"])

    def test_run_requires_lead_id(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["run"])

    def test_import_parses_csv(self):
        parser = build_parser()
        args = parser.parse_args(["import", "--csv", "leads.csv"])
        assert args.command == "import"
        assert args.csv == "leads.csv"

    def test_list_parses_status(self):
        parser = build_parser()
        args = parser.parse_args(["list", "--status", "new"])
        assert args.command == "list"
        assert args.status == "new"

    def test_run_parses_lead_id(self):
        parser = build_parser()
        args = parser.parse_args(["run", "--lead-id", "42"])
        assert args.command == "run"
        assert args.lead_id == 42

    def test_run_all_default_status(self):
        parser = build_parser()
        args = parser.parse_args(["run-all"])
        assert args.command == "run-all"
        assert args.status == "new"


class TestImportCommand:
    def test_import_happy_path(self, tmp_path, monkeypatch, capsys):
        csv_file = tmp_path / "leads.csv"
        _write_csv(
            csv_file,
            ["company_name", "contact_name", "contact_title", "email", "source"],
            [
                ["Acme", "John", "Manager", "john@acme.co.za", "apollo"],
                ["Beta", "Jane", "Director", "jane@beta.co.za", "apollo"],
            ],
        )
        db_path = str(tmp_path / "test.db")
        monkeypatch.setenv("DB_PATH", db_path)

        main(["import", "--csv", str(csv_file)])

        output = capsys.readouterr().out
        assert "2 leads imported" in output
        assert "0 skipped" in output

    def test_import_duplicates_skipped(self, tmp_path, monkeypatch, capsys):
        csv_file = tmp_path / "leads.csv"
        _write_csv(
            csv_file,
            ["company_name", "contact_name", "contact_title", "email", "source"],
            [["Acme", "John", "Manager", "john@acme.co.za", "apollo"]],
        )
        db_path = str(tmp_path / "test.db")
        monkeypatch.setenv("DB_PATH", db_path)

        main(["import", "--csv", str(csv_file)])
        main(["import", "--csv", str(csv_file)])

        output = capsys.readouterr().out
        assert "1 skipped as duplicates" in output


class TestListCommand:
    def test_list_shows_leads(self, tmp_path, monkeypatch, capsys):
        db_path = tmp_path / "test.db"
        monkeypatch.setenv("DB_PATH", str(db_path))

        conn = init_db(db_path)
        insert_lead(conn, _make_lead())
        conn.close()

        main(["list"])

        output = capsys.readouterr().out
        assert "Acme Engineering" in output
        assert "Total: 1" in output

    def test_list_empty(self, tmp_path, monkeypatch, capsys):
        db_path = tmp_path / "test.db"
        monkeypatch.setenv("DB_PATH", str(db_path))
        init_db(db_path).close()

        main(["list"])

        output = capsys.readouterr().out
        assert "No leads found" in output


class TestRunCommand:
    def test_run_missing_lead_exits(self, tmp_path, monkeypatch):
        db_path = tmp_path / "test.db"
        monkeypatch.setenv("DB_PATH", str(db_path))
        init_db(db_path).close()

        with pytest.raises(SystemExit):
            main(["run", "--lead-id", "999"])
