#!/usr/bin/env python3
"""Refresh the EOL data in eol/eol.json.

The script reads the dependencies from the tap formulae, fetches the live state
from the Homebrew formula API, and merges the result into eol/eol.json.

Human fields (note, replacement) are preserved. Machine fields (versions,
dates, status) are always overwritten.

Usage:
    python3 eol/check.py            # print the report, change nothing
    python3 eol/check.py --write    # update eol/eol.json
    python3 eol/check.py --check    # exit 1 if eol.json is stale
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EOL_FILE = ROOT / "eol" / "eol.json"
FORMULA_DIR = ROOT / "Formula"

HOMEBREW_API = "https://formulae.brew.sh/api/formula/{}.json"
FREEUNIT_VERSION = "https://raw.githubusercontent.com/freeunitorg/freeunit/refs/heads/{branch}/version"
FREEUNIT_BRANCH = "https://api.github.com/repos/freeunitorg/freeunit/commits/{branch}"
FREEUNIT_TAGS = "https://api.github.com/repos/freeunitorg/freeunit/tags"
NJS_TAGS = "https://api.github.com/repos/freeunitorg/njs/tags"

# homebrew-core aliases that have no formula of their own
ALIASES = {"pkg-config": "pkgconf"}

# fields that a human writes and the script must not touch
HUMAN_FIELDS = ("note", "replacement", "source", "role", "revision")

# fields that change every day, so they must not make the file stale
VOLATILE_FIELDS = ("disable_date_in_days", "deprecation_date_in_days")

USER_AGENT = "homebrew-unit-eol-check"


def http_get(url: str, attempts: int = 3) -> str:
    """Read a URL. The API answers with 503 when it is busy, so retry it."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last_error = None
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as error:
            last_error = error
            if error.code != 503:
                raise
        except urllib.error.URLError as error:
            last_error = error
        time.sleep(2 ** attempt)
    raise last_error


def tap_formula_names() -> set[str]:
    """The names of the formulae that this tap provides.

    A dependency on one of them is a link inside the tap. It is not a
    package of homebrew-core, so the API has no data for it.
    """
    names = {path.stem for path in FORMULA_DIR.glob("*.rb")}
    aliases = ROOT / "Aliases"
    if aliases.is_dir():
        names.update(entry.name for entry in aliases.iterdir())
    return names


def days_left(date_string: str | None) -> int | None:
    if not date_string:
        return None
    year, month, day = map(int, date_string.split("-"))
    target = datetime.date(year, month, day)
    return (target - datetime.date.today()).days


def status_of(entry: dict) -> str:
    if entry.get("disabled"):
        return "disabled"
    if entry.get("disable_date"):
        return "scheduled_for_disable"
    if entry.get("deprecation_date"):
        return "deprecated"
    return "active"


def core_php_formula(series: str, core_php_version: str) -> str:
    """Return the homebrew-core formula that holds the PHP series.

    The unversioned formula of homebrew-core holds the newest series. A
    versioned formula holds an older one. The series of the newest release
    has no versioned formula in homebrew-core yet.
    """
    if core_php_version.startswith(f"{series}."):
        return "php"
    return f"php@{series}"


def stable_packages(packages: dict) -> dict:
    """Drop the fields that change every day."""
    return {
        name: {key: value for key, value in entry.items()
               if key not in VOLATILE_FIELDS}
        for name, entry in packages.items()
    }


def read_dependencies() -> dict[str, set[str]]:
    usage: dict[str, set[str]] = {}
    pattern = re.compile(r'^\s*(?:depends_on|uses_from_macos)\s+"([^"]+)"', re.M)
    for formula in sorted(FORMULA_DIR.glob("*.rb")):
        for match in pattern.finditer(formula.read_text()):
            usage.setdefault(match.group(1), set()).add(formula.name)
    return usage


def fetch_formula(name: str) -> dict:
    data = json.loads(http_get(HOMEBREW_API.format(name)))
    return {
        "current_version": data.get("versions", {}).get("stable"),
        "deprecated": bool(data.get("deprecated")),
        "deprecation_date": data.get("deprecation_date"),
        "disabled": bool(data.get("disabled")),
        "disable_date": data.get("disable_date"),
    }


def fetch_packages(usage: dict[str, set[str]], previous: dict) -> dict:
    packages = {}
    tap_names = tap_formula_names()
    for dependency in sorted(usage):
        if dependency in tap_names:
            continue
        real = ALIASES.get(dependency, dependency)
        try:
            entry = fetch_formula(real)
        except (urllib.error.URLError, KeyError, ValueError) as error:
            print(f"error: cannot fetch {real}: {error}", file=sys.stderr)
            entry = {"error": str(error)}
        entry["used_by"] = sorted(usage[dependency])
        if real != dependency:
            entry["alias_of"] = real
        old = previous.get(dependency, {})
        for field in HUMAN_FIELDS:
            if field in old:
                entry[field] = old[field]
        if entry.get("disable_date"):
            entry["disable_date_in_days"] = days_left(entry["disable_date"])
        if entry.get("deprecation_date"):
            entry["deprecation_date_in_days"] = days_left(entry["deprecation_date"])
        entry["status"] = status_of(entry)
        packages[dependency] = entry
    return packages


def tap_formula_versions(core_php: str) -> dict[str, dict]:
    unit_source = (FORMULA_DIR / "unit.rb").read_text()
    branch = re.search(r'url "[^"]+",\s*\n\s*branch:\s+"([^"]+)"', unit_source).group(1)
    unit_revision = re.search(r'revision:\s+"([^"]+)"', unit_source).group(1)
    njs_tag = re.search(r'resource "njs".*?tag:\s+"([^"]+)"', unit_source, re.S).group(1)
    njs_revision = re.search(r'resource "njs".*?revision:\s+"([^"]+)"',
                             unit_source, re.S).group(1)

    unit_tags = json.loads(http_get(FREEUNIT_TAGS))
    release_tags = [t["name"] for t in unit_tags
                    if not t["name"].startswith(("v", "unitctl/"))]
    njs_tags = [t["name"] for t in json.loads(http_get(NJS_TAGS))]

    branch_version = re.search(r"NXT_VERSION=(\S+)",
                                http_get(FREEUNIT_VERSION.format(branch=branch))).group(1)
    branch_head = json.loads(
      http_get(FREEUNIT_BRANCH.format(branch=branch)),
    )["sha"]

    formulae = {
        "unit": {
            "current_version": branch_version,
            "upstream_latest_tag": release_tags[0] if release_tags else None,
            "upstream_branch_version": branch_version,
            "upstream_branch": branch,
            "pinned_revision": unit_revision,
            "status": "matches_upstream_branch"
            if unit_revision == branch_head else "behind_upstream_branch",
        },
        "njs": {
            "current_version": njs_tag,
            "upstream_latest_tag": njs_tags[0] if njs_tags else None,
            "status": "current" if njs_tags and njs_tags[0] == njs_tag else "behind_upstream",
        },
    }

    # Every php embed formula pins one PHP series. Compare each series with
    # the formula of homebrew-core that has the same series.
    for path in sorted(FORMULA_DIR.glob("php-embed*.rb")):
        source = path.read_text()
        match = re.search(r"php-(\d+\.\d+\.\d+)\.tar\.xz", source)
        if not match:
            continue
        version = match.group(1)
        series = ".".join(version.split(".")[:2])
        core_formula = core_php_formula(series, core_php)
        core_series_version = fetch_formula(core_formula)["current_version"]
        formulae[path.stem] = {
            "current_version": version,
            "homebrew_core_php_formula": core_formula,
            "homebrew_core_php_series_version": core_series_version,
            "homebrew_core_php": core_php,
            "status": "matches_core_php_series" if core_series_version == version
            else "differs_from_core_php_series",
        }

    return formulae


def check_version_coherence(core_php_version: str) -> list[str]:
    """Verify that every PHP formula pins the matching PHP series."""
    problems = []

    for path in sorted(FORMULA_DIR.glob("php-embed@*.rb")):
        series = path.stem.split("@")[1]
        source = path.read_text()
        version = re.search(r"php-(\d+\.\d+\.\d+)\.tar\.xz", source).group(1)
        if not version.startswith(series + "."):
            problems.append(f"{path.name}: builds PHP {version}, expected the {series} series")
        if f'depends_on "php@{series}"' not in source:
            problems.append(f"{path.name}: must depend on php@{series}")

    for path in sorted(FORMULA_DIR.glob("unit-php@*.rb")):
        series = path.stem.split("@")[1]
        source = path.read_text()
        if f'depends_on "php-embed@{series}"' not in source:
            problems.append(f"{path.name}: must depend on php-embed@{series}")
        if f'formula_opt_lib("php-embed@{series}")' not in source:
            problems.append(f"{path.name}: must link the php-embed@{series} library")
        if f'formula_opt_bin("php@{series}")' not in source:
            problems.append(f"{path.name}: must use the php@{series} php-config")
        module = "php" + series.replace(".", "")
        if f'"--module={module}"' not in source:
            problems.append(f"{path.name}: must set --module={module}")
        if f'"make", "{module}-install"' not in source:
            problems.append(f"{path.name}: must build the {module}-install target")

    # The unversioned formula follows the newest series of homebrew-core. The
    # core formula of that series is the unversioned php formula, until
    # homebrew-core adds a versioned formula for it.
    embed_source = (FORMULA_DIR / "php-embed.rb").read_text()
    embed_version = re.search(r"php-(\d+\.\d+\.\d+)\.tar\.xz", embed_source).group(1)
    embed_series = ".".join(embed_version.split(".")[:2])
    core = core_php_formula(embed_series, core_php_version)

    for path in sorted(FORMULA_DIR.glob("unit-php.rb")):
        source = path.read_text()
        if f'formula_opt_bin("{core}")' not in source:
            problems.append(f"{path.name}: must use the {core} php-config")
        if 'formula_opt_lib("php-embed")' not in source:
            problems.append(f"{path.name}: must link the php-embed library")
        if '"--module=php"' not in source:
            problems.append(f"{path.name}: must set --module=php")
        if '"make", "php-install"' not in source:
            problems.append(f"{path.name}: must build the php-install target")

    for path in sorted(FORMULA_DIR.glob("php-embed.rb")):
        source = path.read_text()
        if f'depends_on "{core}"' not in source:
            problems.append(f"{path.name}: builds PHP {embed_version} "
                            f"but does not depend on {core}")
        if "unit-php@" in source:
            problems.append(f"{path.name}: must not depend on a versioned unit module")

    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="update eol/eol.json")
    parser.add_argument("--check", action="store_true", help="exit 1 if eol.json is stale")
    args = parser.parse_args()

    core_php = fetch_formula("php")["current_version"]
    problems = check_version_coherence(core_php)
    for problem in problems:
        print(f"error: {problem}", file=sys.stderr)
    if problems:
        return 1

    document = json.loads(EOL_FILE.read_text())
    previous_packages = document.get("packages", {})
    previous_formulae = document.get("tap_formulae", {})

    packages = fetch_packages(read_dependencies(), previous_packages)
    formulae = tap_formula_versions(core_php)
    for name, entry in formulae.items():
        for field in HUMAN_FIELDS:
            if field in previous_formulae.get(name, {}):
                entry[field] = previous_formulae[name][field]

    document["packages"] = packages
    document["tap_formulae"] = formulae
    document["_checked"] = datetime.date.today().isoformat()

    print(f"packages: {len(packages)}, tap formulae: {len(formulae)}")
    for name, entry in packages.items():
        marker = {"disabled": "DISABLED", "scheduled_for_disable": "scheduled",
                  "deprecated": "deprecated"}.get(entry.get("status"), "")
        print(f"  {name:16} {entry.get('current_version', '-'):14} {marker}")

    changed = (stable_packages(packages) != stable_packages(previous_packages)
               or formulae != previous_formulae)

    if args.write:
        EOL_FILE.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n")
        print(f"wrote {EOL_FILE}")
        return 0

    if args.check:
        if changed:
            print("eol/eol.json is stale. Run: python3 eol/check.py --write",
                  file=sys.stderr)
            return 1
        print("eol/eol.json is up to date")
        return 0

    if changed:
        print("eol/eol.json differs from the live data. Run with --write to update.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
