"""Back up the gitignored live runtime state of the Operations and Pappa T vaults.

This data is the only thing in the DCOE system with no second copy: git never
captured it by design. See docs/specs/2026-08-06-runtime-data-backup-script.md
and knowledge/operations-hub.md.

Usage:
    python scripts/backup-runtime-data.py [--dry-run] [--quiet] [--keep N]

Exit codes:
    0  everything backed up and verified
    1  one or more files failed to back up or verify
    2  the data/secret separation invariant was violated (should never happen)
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

HOME = Path.home()
VAULTS = [Path(r"C:\Users\tlelo\Desktop\Operations"), Path(r"C:\Users\tlelo\Desktop\Pappa T")]

DATA_LOCAL_ROOT = HOME / "Backups" / "dcoe-runtime"
DATA_SYNCED_ROOT = HOME / "OneDrive" / "DCOE-Backups"
SECRETS_LOCAL_ROOT = HOME / "Backups" / "dcoe-secrets"

PRUNE_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__", ".next",
    ".ruff_cache", ".pytest_cache", ".mypy_cache", ".obsidian", ".qwen",
    "dist", "build", ".turbo",
}
PRUNE_SUFFIXES = (".egg-info",)

DATA_PATTERNS = ("*.db", "*.sqlite", "*.sqlite3")
# Dated safety copies alongside a live DB, e.g. sops.db.pre-batch34-backup-...
# These do not match *.db, so an earlier version of this script silently
# dropped them. They are rollback points with no other copy - keep them.
SNAPSHOT_PATTERNS = ("*.db.*", "*.sqlite.*", "*.sqlite3.*")
SECRET_PATTERNS = (".env", ".env.*", "credentials*.json", "token*.json", "*.pem", "*.pfx", "*.key")
SECRET_EXCLUDE = ("*.example", "*.example.*", "*.sample")
AGENT_MEMORY_DIRNAME = "agent-memory"


class _Tee:
    """Write to the console and a log file at once, so a scheduled run leaves a trail."""

    def __init__(self, stream, path: Path):
        self._stream = stream
        self._fh = open(path, "a", encoding="utf-8")

    def write(self, text: str) -> int:
        self._stream.write(text)
        self._fh.write(text)
        self._fh.flush()
        return len(text)

    def flush(self) -> None:
        self._stream.flush()
        self._fh.flush()


def log(msg: str, quiet: bool = False) -> None:
    if not quiet:
        print(msg)


def should_prune(d: Path) -> bool:
    if d.name in PRUNE_DIRS or d.name.endswith(PRUNE_SUFFIXES):
        return True
    # .claude/worktrees/ holds live git worktrees - separate checkouts of a repo
    # already covered here. Descending into them backs up every match a second
    # and third time (observed 2026-08-06: one .pfx found three times).
    return d.name == "worktrees" and d.parent.name == ".claude"


def matches(name: str, patterns) -> bool:
    return any(fnmatch.fnmatch(name, p) for p in patterns)


def classify(path: Path) -> str | None:
    name = path.name
    if matches(name, SECRET_EXCLUDE):
        return None
    if matches(name, SECRET_PATTERNS):
        return "SECRET"
    if matches(name, DATA_PATTERNS):
        return "DATA"
    if matches(name, SNAPSHOT_PATTERNS):
        return "SNAPSHOT"
    return None


def discover(vaults):
    """Walk the vaults, pruning regenerable trees.

    Returns (data, snapshots, secrets, memory_dirs).
    """
    data, snapshots, secrets, memory_dirs = [], [], [], []
    for root in vaults:
        if not root.exists():
            continue
        stack = [root]
        while stack:
            cur = stack.pop()
            try:
                entries = list(cur.iterdir())
            except (PermissionError, OSError):
                continue
            for e in entries:
                if e.is_dir():
                    if e.name == AGENT_MEMORY_DIRNAME:
                        memory_dirs.append(e)
                        continue
                    if not should_prune(e):
                        stack.append(e)
                elif e.is_file():
                    kind = classify(e)
                    if kind == "DATA":
                        data.append(e)
                    elif kind == "SNAPSHOT":
                        snapshots.append(e)
                    elif kind == "SECRET":
                        secrets.append(e)
    return sorted(data), sorted(snapshots), sorted(secrets), sorted(memory_dirs)


def rel_to_desktop(p: Path) -> str:
    try:
        return p.relative_to(Path(r"C:\Users\tlelo\Desktop")).as_posix()
    except ValueError:
        return p.as_posix()


def flat_name(rel: str) -> str:
    return rel.replace("/", "__").replace(" ", "_")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def table_counts(db_path: Path) -> dict:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        names = [
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]
        return {n: conn.execute(f'SELECT count(*) FROM "{n}"').fetchone()[0] for n in names}
    finally:
        conn.close()


def backup_db(src: Path, dst: Path) -> tuple[bool, str]:
    """Copy via the sqlite backup API, then verify integrity and row counts."""
    try:
        s = sqlite3.connect(f"file:{src}?mode=ro", uri=True)
        d = sqlite3.connect(dst)
        try:
            with d:
                s.backup(d)
            integrity = d.execute("PRAGMA integrity_check").fetchone()[0]
        finally:
            s.close()
            d.close()
        if integrity != "ok":
            return False, f"integrity_check={integrity}"
        before, after = table_counts(src), table_counts(dst)
        if before != after:
            diff = {k: (before.get(k), after.get(k)) for k in set(before) | set(after)
                    if before.get(k) != after.get(k)}
            return False, f"row-count mismatch {diff}"
        return True, f"ok, {len(after)} tables, {sum(after.values()):,} rows"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def prune_old(root: Path, keep: int, quiet: bool) -> None:
    if not root.exists():
        return
    runs = sorted((d for d in root.iterdir() if d.is_dir()), key=lambda d: d.name)
    for old in runs[:-keep] if keep > 0 else []:
        shutil.rmtree(old, ignore_errors=True)
        log(f"  pruned  {old.name}", quiet)


def load_previous_manifest(root: Path) -> set:
    if not root.exists():
        return set()
    runs = sorted((d for d in root.iterdir() if d.is_dir()), key=lambda d: d.name)
    for run in reversed(runs):
        f = run / "manifest.json"
        if f.exists():
            try:
                return set(json.loads(f.read_text(encoding="utf-8")).get("discovered", []))
            except (ValueError, OSError):
                continue
    return set()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="report what would be backed up, write nothing")
    ap.add_argument("--quiet", action="store_true", help="suppress per-file output (for scheduled runs)")
    ap.add_argument("--keep", type=int, default=7, help="how many runs to retain per destination (default 7)")
    ap.add_argument("--log-file", type=Path, help="append this run's output to a file (for scheduled runs)")
    args = ap.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")

    if args.log_file:
        args.log_file.parent.mkdir(parents=True, exist_ok=True)
        sys.stdout = sys.stderr = _Tee(sys.stdout, args.log_file)
        print(f"\n{'=' * 72}\nrun started {datetime.now():%Y-%m-%d %H:%M:%S}\n{'=' * 72}")
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    failures: list[str] = []

    data_files, snapshot_files, secret_files, memory_dirs = discover(VAULTS)
    discovered = sorted(
        [rel_to_desktop(p) for p in data_files]
        + [rel_to_desktop(p) for p in snapshot_files]
        + [rel_to_desktop(p) for p in secret_files]
        + [rel_to_desktop(p) for p in memory_dirs]
    )

    previous = load_previous_manifest(DATA_LOCAL_ROOT)
    if previous:
        added = sorted(set(discovered) - previous)
        removed = sorted(previous - set(discovered))
        if added or removed:
            log("=== drift since last run ===", args.quiet)
            for a in added:
                log(f"  NEW      {a}", args.quiet)
            for r in removed:
                log(f"  GONE     {r}", args.quiet)
            log("", args.quiet)

    if args.dry_run:
        log(f"=== dry run: {len(data_files)} databases, {len(snapshot_files)} snapshots, "
            f"{len(secret_files)} secrets, {len(memory_dirs)} agent-memory trees ===", args.quiet)
        for p in data_files:
            size = p.stat().st_size
            note = "  (empty, would skip)" if size == 0 else ""
            log(f"  DATA    {size:>10,}  {rel_to_desktop(p)}{note}", args.quiet)
        for p in snapshot_files:
            log(f"  SNAP    {p.stat().st_size:>10,}  {rel_to_desktop(p)}", args.quiet)
        for p in secret_files:
            log(f"  SECRET  {p.stat().st_size:>10,}  {rel_to_desktop(p)}", args.quiet)
        for p in memory_dirs:
            log(f"  MEMORY              {rel_to_desktop(p)}", args.quiet)
        return 0

    data_local = DATA_LOCAL_ROOT / stamp
    secrets_local = SECRETS_LOCAL_ROOT / stamp
    (data_local / "databases").mkdir(parents=True, exist_ok=True)
    (data_local / "agent-memory").mkdir(parents=True, exist_ok=True)
    secrets_local.mkdir(parents=True, exist_ok=True)

    manifest_rows = []
    log("=== databases (sqlite backup API + verify) ===", args.quiet)
    for src in data_files:
        rel = rel_to_desktop(src)
        if src.stat().st_size == 0:
            log(f"  skip     empty        {rel}", args.quiet)
            continue
        dst = data_local / "databases" / flat_name(rel)
        ok, detail = backup_db(src, dst)
        if ok:
            manifest_rows.append((rel, dst.name, dst.stat().st_size, sha256(dst), detail))
            log(f"  ok       {dst.stat().st_size:>10,}  {rel}  ({detail})", args.quiet)
        else:
            failures.append(f"{rel}: {detail}")
            log(f"  FAILED   {rel}: {detail}", args.quiet)

    log("\n=== historical snapshots (plain copy - static, not live) ===", args.quiet)
    snap_dir = data_local / "databases" / "historical-snapshots"
    snap_dir.mkdir(exist_ok=True)
    for src in snapshot_files:
        rel = rel_to_desktop(src)
        try:
            shutil.copy2(src, snap_dir / flat_name(rel))
            log(f"  ok       {src.stat().st_size:>10,}  {rel}", args.quiet)
        except Exception as exc:
            failures.append(f"{rel}: {exc}")
            log(f"  FAILED   {rel}: {exc}", args.quiet)

    log("\n=== agent memory ===", args.quiet)
    for src in memory_dirs:
        rel = rel_to_desktop(src)
        dst = data_local / "agent-memory" / flat_name(rel)
        try:
            shutil.copytree(src, dst, dirs_exist_ok=True)
            n = sum(1 for f in dst.rglob("*") if f.is_file())
            log(f"  ok       {n} files   {rel}", args.quiet)
        except Exception as exc:
            failures.append(f"{rel}: {exc}")
            log(f"  FAILED   {rel}: {exc}", args.quiet)

    log("\n=== secrets (local only, never synced) ===", args.quiet)
    for src in secret_files:
        rel = rel_to_desktop(src)
        dst = secrets_local / flat_name(rel)
        try:
            shutil.copy2(src, dst)
            log(f"  ok       {dst.stat().st_size:>10,}  {rel}", args.quiet)
        except Exception as exc:
            failures.append(f"{rel}: {exc}")
            log(f"  FAILED   {rel}: {exc}", args.quiet)

    (data_local / "manifest.json").write_text(
        json.dumps(
            {
                "stamp": stamp,
                "discovered": discovered,
                "databases": [
                    {"source": r, "file": f, "bytes": b, "sha256": h, "verified": d}
                    for r, f, b, h, d in manifest_rows
                ],
                "secrets_location": str(secrets_local),
                "failures": failures,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    lines = [
        f"# DCOE runtime-data backup — {stamp}",
        "",
        "Gitignored live runtime state from Desktop/Operations and Desktop/Pappa T.",
        "Git never captured these by design, so this is their only copy.",
        "",
        "Databases were copied with Python's sqlite3 backup API, which stays",
        "consistent even if the source is being written to, then verified with",
        "PRAGMA integrity_check and a per-table row-count comparison.",
        "",
        f"Secrets are NOT here. They are local-only at: {secrets_local}",
        "",
        "| source | file | bytes | verified | sha256 |",
        "|---|---|---|---|---|",
    ]
    for r, f, b, h, d in manifest_rows:
        lines.append(f"| `{r}` | `{f}` | {b:,} | {d} | `{h[:16]}…` |")
    lines += [
        "",
        "## Restore",
        "",
        "Copy the file back to its source path above. The flattened name encodes",
        "the original path: `__` was `/`, `_` was a space.",
        "",
    ]
    if failures:
        lines += ["## Failures", ""] + [f"- {x}" for x in failures] + [""]
    (data_local / "MANIFEST.md").write_text("\n".join(lines), encoding="utf-8")

    data_synced = DATA_SYNCED_ROOT / stamp
    data_synced.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(data_local, data_synced, dirs_exist_ok=True)

    (secrets_local / "README.md").write_text(
        "\n".join(
            [
                f"# Secrets backup — {stamp}",
                "",
                "Live credentials from Desktop/Operations and Desktop/Pappa T.",
                "",
                "**Local-only by design.** Do not move this into OneDrive, a git repo,",
                "or any synced location. The database backup is at",
                f"{data_local} and is safe to sync; this is not.",
                "",
                "Flattened names encode the original path: `__` was `/`, `_` was a space.",
                "",
            ]
            + [f"- `{flat_name(rel_to_desktop(p))}` <- `{rel_to_desktop(p)}`" for p in secret_files]
        ),
        encoding="utf-8",
    )

    leaked = [
        p for p in data_synced.rglob("*")
        if p.is_file() and classify(p) == "SECRET"
    ]
    if leaked:
        for p in leaked:
            print(f"INVARIANT VIOLATED: secret-classified file in synced tree: {p}")
        return 2

    log("\n=== retention ===", args.quiet)
    for root in (DATA_LOCAL_ROOT, DATA_SYNCED_ROOT, SECRETS_LOCAL_ROOT):
        prune_old(root, args.keep, args.quiet)

    def tree_size(p: Path) -> int:
        return sum(f.stat().st_size for f in p.rglob("*") if f.is_file())

    log("\n=== result ===", args.quiet)
    log(f"  data (local)     {data_local}  [{tree_size(data_local):,} bytes]", args.quiet)
    log(f"  data (synced)    {data_synced}  [{tree_size(data_synced):,} bytes]", args.quiet)
    log(f"  secrets (local)  {secrets_local}  [{tree_size(secrets_local):,} bytes]", args.quiet)

    if failures:
        print(f"COMPLETED WITH {len(failures)} FAILURE(S):")
        for x in failures:
            print(f"  - {x}")
        return 1
    log("  all files backed up and verified", args.quiet)
    return 0


if __name__ == "__main__":
    sys.exit(main())
