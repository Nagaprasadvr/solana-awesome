#!/usr/bin/env python3
"""Report crates.io state for solana-awesome: available version bumps for
existing dependencies, and new solana-* crates we don't re-export yet.

Read-only: prints a markdown report to stdout and never edits the repo.
The /update-crates skill consumes this report and applies changes.

Trust model: a crate is a candidate only if it shares an owner (user or
team) with TRUST_ANCHOR, so name-squatters never show up. Crates listed in
scripts/crates-denylist.txt (one name per line, `#` comments) are skipped,
as are crates with placeholder descriptions or no release in 18 months.

Usage: python3 scripts/check_crates.py
"""

import datetime
import json
import re
import sys
import time
import tomllib
import urllib.error
import urllib.request
from pathlib import Path

API = "https://crates.io/api/v1"
HEADERS = {
    "User-Agent": "solana-awesome-update-agent (https://github.com/Nagaprasadvr/solana-awesome)"
}
# Owners of this crate define the trusted publisher set.
TRUST_ANCHOR = "solana-pubkey"
REPO_ROOT = Path(__file__).resolve().parent.parent
DENYLIST_PATH = REPO_ROOT / "scripts" / "crates-denylist.txt"
REQUEST_INTERVAL = 0.5  # crates.io crawler policy: stay well under 1 req/s
# Crates with no release in this window are considered abandoned.
STALE_AFTER_DAYS = 18 * 30
PLACEHOLDER_RE = re.compile(r"reserved for future use|placeholder", re.IGNORECASE)


def get(path: str) -> dict:
    time.sleep(REQUEST_INTERVAL)
    req = urllib.request.Request(f"{API}{path}", headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        sys.exit(f"error: GET {path} failed: {e.code} {e.reason}")


def load_deps() -> dict[str, str]:
    with open(REPO_ROOT / "Cargo.toml", "rb") as f:
        manifest = tomllib.load(f)
    deps = {}
    for name, spec in manifest.get("dependencies", {}).items():
        if name.startswith("solana-"):
            deps[name] = spec["version"] if isinstance(spec, dict) else spec
    return deps


def load_denylist() -> set[str]:
    if not DENYLIST_PATH.exists():
        return set()
    names = set()
    for line in DENYLIST_PATH.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            names.add(line)
    return names


def req_covers(req: str, version: str) -> bool:
    """True if the latest version still matches the manifest's caret-style
    requirement prefix, e.g. req "4" covers "4.3.1" but not "5.0.0"."""
    req_parts = req.split(".")
    ver_parts = version.split(".")
    return ver_parts[: len(req_parts)] == req_parts


def check_bumps(deps: dict[str, str]) -> list[dict]:
    bumps = []
    for name, req in sorted(deps.items()):
        info = get(f"/crates/{name}")["crate"]
        latest = info.get("max_stable_version") or info["max_version"]
        if not req_covers(req, latest):
            bumps.append({"name": name, "req": req, "latest": latest})
    return bumps


def trusted_owner_ids() -> tuple[list[dict], list[dict]]:
    users = get(f"/crates/{TRUST_ANCHOR}/owner_user").get("users", [])
    teams = get(f"/crates/{TRUST_ANCHOR}/owner_team").get("teams", [])
    return users, teams


def crates_owned_by(param: str, owner_id: int) -> dict[str, dict]:
    """All solana-* crates for one owner, keyed by name."""
    found = {}
    page = 1
    while True:
        data = get(f"/crates?{param}={owner_id}&per_page=100&page={page}&sort=alpha")
        for c in data.get("crates", []):
            if c["name"].startswith("solana-"):
                found[c["name"]] = c
        if data.get("meta", {}).get("next_page") and data.get("crates"):
            page += 1
        else:
            return found


def is_live(crate: dict, stale_cutoff: str) -> bool:
    return (
        crate.get("max_stable_version") is not None
        and crate.get("updated_at", "") >= stale_cutoff
        and not PLACEHOLDER_RE.search(crate.get("description") or "")
    )


def main() -> None:
    deps = load_deps()
    denylist = load_denylist()
    stale_cutoff = (
        datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=STALE_AFTER_DAYS)
    ).strftime("%Y-%m-%d")

    print("# solana-awesome crates.io report\n")

    bumps = check_bumps(deps)
    print("## Version bumps available\n")
    if bumps:
        print("| Crate | Manifest req | Latest stable |")
        print("|---|---|---|")
        for b in bumps:
            print(f"| `{b['name']}` | `{b['req']}` | `{b['latest']}` |")
    else:
        print(f"None — all {len(deps)} dependency requirements cover the latest stable versions.")
    print()

    users, teams = trusted_owner_ids()
    owner_names = [u["login"] for u in users] + [t["login"] for t in teams]
    candidates: dict[str, dict] = {}
    for u in users:
        candidates.update(crates_owned_by("user_id", u["id"]))
    for t in teams:
        candidates.update(crates_owned_by("team_id", t["id"]))

    new = {
        name: c
        for name, c in candidates.items()
        if name not in deps and name not in denylist and is_live(c, stale_cutoff)
    }

    print(f"## New crate candidates ({len(new)})\n")
    print(f"Trusted owners (from `{TRUST_ANCHOR}`): {', '.join(f'`{n}`' for n in owner_names)}\n")
    if new:
        print("| Crate | Latest | Downloads | Description |")
        print("|---|---|---|---|")
        for name in sorted(new):
            c = new[name]
            desc = (c.get("description") or "").replace("|", "\\|").replace("\n", " ").strip()
            print(f"| `{name}` | `{c['max_stable_version']}` | {c['downloads']:,} | {desc} |")
    else:
        print("None — every trusted solana-* crate is already re-exported, denylisted, or filtered.")
    print()
    included = len(deps.keys() & candidates.keys())
    denied = len(denylist & candidates.keys())
    filtered = len(candidates) - len(new) - included - denied
    print(f"({len(candidates)} trusted crates total: {included} already included, "
          f"{denied} denylisted, {filtered} filtered as stale/placeholder.)")


if __name__ == "__main__":
    main()
