#!/usr/bin/env bash
# Run the local checks of the tap.
#
# The script runs the same checks as the CI job "check-generate".
# It also runs the two Python checks of this repository.
#
# Usage:
#   test/run-checks.sh            run the checks
#   test/run-checks.sh --eol      run the checks and the EOL check
#
set -euo pipefail

REPO_DIR="${HOMEBREW_UNIT_REPO:-/home/brew/homebrew-unit}"

if [[ ! -d "${REPO_DIR}" ]]
then
  echo "error: the repository is not at ${REPO_DIR}" >&2
  echo "Mount it with: docker run --rm -v \"\$PWD:${REPO_DIR}\" homebrew-unit-test" >&2
  exit 2
fi

# Use the scripts of the working copy. Fall back to the copy in the image
# when the working copy does not hold the test directory.
SCRIPT_DIR="${REPO_DIR}/test"
if [[ ! -f "${SCRIPT_DIR}/check-components-order.py" ]]
then
  SCRIPT_DIR="/opt/homebrew-unit-test"
fi

cd "${REPO_DIR}"

RUN_EOL=false
if [[ "${1:-}" == "--eol" ]]
then
  RUN_EOL=true
fi

# The tap name comes from the remote. A fork has another owner than the tap
# on GitHub, so the name must not be hard coded.
REMOTE_URL="$(git -c safe.directory='*' remote get-url origin)"
REMOTE_URL="${REMOTE_URL%.git}"
OWNER="$(echo "${REMOTE_URL}" | sed -E 's#^.*github\.com[:/]+([^/]+)/.*$#\1#')"
REPO="$(echo "${REMOTE_URL}" | sed -E 's#^.*github\.com[:/]+[^/]+/([^/]+)$#\1#')"

# The tap "owner/unit" lives in the directory "owner/homebrew-unit".
TAP="${OWNER}/${REPO#homebrew-}"
TAP_DIR_NAME="${OWNER}/${REPO}"

echo "==> Tap: ${TAP}"
echo "==> Repository: ${REPO_DIR}"

# Point the tap at this working copy. A symlink keeps the link live, so
# Homebrew checks the files in this directory and not a copy of them.
TAPS_DIR="$(brew --repository)/Library/Taps"
mkdir -p "${TAPS_DIR}/${OWNER}"
rm -rf "${TAPS_DIR:?}/${TAP_DIR_NAME:?}"
ln -s "${REPO_DIR}" "${TAPS_DIR}/${TAP_DIR_NAME}"

# Homebrew 4.6 and later load a tap only when it is trusted. The CI job does
# the same.
brew trust "${TAP}" >/dev/null 2>&1 || true

status=0

echo
echo "==> brew style"
brew style "${TAP}" || status=1

echo
echo "==> brew readall"
brew readall --aliases --os=all --arch=all "${TAP}" || status=1

echo
echo "==> brew audit"
brew audit --except=installed --tap="${TAP}" || status=1

echo
echo "==> Component order"
python3 "${SCRIPT_DIR}/check-components-order.py" "${REPO_DIR}/Formula" || status=1

if [[ "${RUN_EOL}" == true ]]
then
  echo
  echo "==> EOL state"
  python3 "${REPO_DIR}/eol/check.py" --check || status=1
fi

echo
if [[ "${status}" -eq 0 ]]
then
  echo "All checks passed."
else
  echo "Some checks failed." >&2
fi
exit "${status}"
