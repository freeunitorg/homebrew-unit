#!/usr/bin/env python3
"""Check that the patch of every php embed formula applies to its source.

The php embed formulae carry a patch that fixes the linking of the system
libraries of macOS. The patch is applied to the source of the PHP version of
the formula. A patch with the context of the wrong series fails the build
with the message "1 out of 2 hunks failed".

This script reads the patch from the formula, downloads the source of the PHP
version of the formula, and applies the patch in the dry run mode. The result
is the same as the result of the build step of the formula.

Usage:
    python3 test/check-patches.py [--cache DIR]
"""
import argparse
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FORMULA_DIR = ROOT / "Formula"

USER_AGENT = "homebrew-unit-patch-check"

# The version of the PHP source comes from the url of the formula.
URL_PATTERN = re.compile(r'url "https://www\.php\.net/distributions/php-(\d+\.\d+\.\d+)\.tar\.xz"')

# The files of the source that the patch touches.
PATCHED_FILES = ("build/php.m4", "configure.ac")


def fetch_tarball(version: str, cache: Path) -> Path:
    """Download the PHP source. Keep it in the cache."""
    cache.mkdir(parents=True, exist_ok=True)
    tarball = cache / f"php-{version}.tar.xz"
    if not tarball.exists():
        url = f"https://www.php.net/distributions/php-{version}.tar.xz"
        print(f"  downloading {url}")
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=120) as response:
            tarball.write_bytes(response.read())
    return tarball


def formula_patch(source: str) -> str:
    """Return the text of the patch of the formula."""
    if "patch :DATA" not in source:
        return ""
    marker = re.search(r"^__END__\n(.*)\Z", source, re.S | re.M)
    return marker.group(1) if marker else ""


def extract_patched_files(tarball: Path, version: str, target: Path) -> bool:
    """Extract the files that the patch touches. Keep the directory of the source."""
    prefix = f"php-{version}"
    found = set()
    with tarfile.open(tarball, "r:xz") as archive:
        for member in archive.getmembers():
            for name in PATCHED_FILES:
                if member.name == f"{prefix}/{name}":
                    member.name = name
                    archive.extract(member, target)
                    found.add(name)
    return found == set(PATCHED_FILES)


def check(path: Path, cache: Path) -> list[str]:
    """Return the list of problems of one formula."""
    source = path.read_text()
    version_match = URL_PATTERN.search(source)
    if not version_match:
        return []

    patch_text = formula_patch(source)
    if not patch_text:
        return []

    version = version_match.group(1)
    tarball = fetch_tarball(version, cache)

    with tempfile.TemporaryDirectory() as workdir:
        work = Path(workdir)
        if not extract_patched_files(tarball, version, work):
            return [f"{path.name}: the patched files are not in the archive of PHP {version}"]

        (work / "change.patch").write_text(patch_text)
        result = subprocess.run(
            # The option -F 0 forbids the fuzz. The patch program of macOS
            # refuses a hunk with a wrong context line, the program of Linux
            # applies it with the fuzz. The build of macOS failed with the
            # message "1 out of 2 hunks failed".
            # The option -N changes nothing, it prints the patch only.
            ["patch", "-g", "0", "-f", "-p1", "-F", "0", "-N"],
            cwd=work,
            input=patch_text,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            output = (result.stdout + result.stderr).strip().replace("\n", " ")
            return [f"{path.name}: the patch does not apply to PHP {version}: {output}"]
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", default=None,
                        help="directory for the downloaded source archives")
    args = parser.parse_args()

    if shutil.which("patch") is None:
        print("error: the program patch is not found", file=sys.stderr)
        return 2

    cache = Path(args.cache) if args.cache else Path(tempfile.gettempdir()) / "php-sources"

    problems = []
    for path in sorted(FORMULA_DIR.glob("php-embed*.rb")):
        print(f"checking {path.name}")
        problems.extend(check(path, cache))

    for problem in problems:
        print(f"error: {problem}", file=sys.stderr)
    print(f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
