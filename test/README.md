# Local test environment

This directory holds a container that runs the checks of the tap. Use it to check a formula before you push it.

The container holds Homebrew on Linux. It runs the same checks as the CI job `check-generate`.

## Files

| File | Purpose |
|---|---|
| `Dockerfile` | The image. It holds Homebrew, rubocop, shellcheck, shfmt, and actionlint. |
| `entrypoint.sh` | Copies the working copy into the container. Then it starts the checks. |
| `run-checks.sh` | Runs the checks. |
| `check-components-order.py` | Checks the order of the formula components. |

## Requirements

- Docker
- A clone of this repository

## Build the image

Run this command once.

```bash
docker build -t homebrew-unit-test test/
```

## Run the checks

Run this command from the root of the repository.

```bash
docker run --rm -v "$PWD:/mnt/homebrew-unit:ro" homebrew-unit-test
```

The command exits with code 0 when all checks pass. The command exits with code 1 when a check fails.

## What the checks do

The script runs four checks. All four checks must pass.

| Check | Purpose |
|---|---|
| `brew style` | Checks the code style of the formulae and the scripts. |
| `brew readall` | Loads every formula. It finds the errors in the formula syntax. |
| `brew audit` | Checks the formulae against the rules of Homebrew. |
| `check-components-order.py` | Checks the order of the formula components. |

The script copies the repository into the container first. The `brew style` command writes to the files that it checks. The files of a mounted directory keep the rights of the user on the host, so the command can not write to them.

## Check the EOL state

Add the `--eol` flag to check the EOL data of the dependencies. This check reads the Homebrew API. It needs a network connection.

```bash
docker run --rm -v "$PWD:/mnt/homebrew-unit:ro" homebrew-unit-test --eol
```

The check reads `eol/eol.json`. It fails when the file differs from the live data.

## Run the component check alone

The component check needs only Python 3. It does not need Docker.

```bash
python3 test/check-components-order.py Formula
```

## Notes

- The tap name comes from the `origin` remote. A fork has another owner than the tap on GitHub.
- The container uses the `brew` user. It does not need `sudo`.
- The image holds the linters. A later run of the container starts fast.
- The container does not change the files on the host. It copies them and it removes the copy at the end.
