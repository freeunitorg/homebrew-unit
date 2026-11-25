# EOL tracking for the FreeUnit Homebrew tap

This directory holds the end-of-life data for every package that the tap depends on.

## Files

| File | Content |
|---|---|
| `eol.json` | The EOL state of all 37 packages and all 3 tap formulae. |
| `check.py` | The script that fetches the live state and updates `eol.json`. |

## Why this file exists

Homebrew disables a versioned formula when the unversioned formula covers it. A disabled formula cannot be installed. The tap build then fails during the dependency step.

The `eol.json` file records the disable date of every dependency. Read it before you change any dependency in `Formula/`.

## Data source

The package data comes from the Homebrew formula API.

```
https://formulae.brew.sh/api/formula/<name>.json
```

The tap versions come from the FreeUnit repository and the njs repository.

## How to read `eol.json`

### `packages`

Each key is a package name. Each entry records the fields below.

| Field | Content |
|---|---|
| `used_by` | The formulae that depend on this package. |
| `current_version` | The version in homebrew-core. |
| `deprecated` | The package is deprecated. Homebrew prints a warning during the install. |
| `deprecation_date` | The date of the deprecation. |
| `disabled` | The package is disabled. The install fails. |
| `disable_date` | The date of the disable. |
| `status` | One of `active`, `deprecated`, `scheduled_for_disable`, `disabled`. |
| `replacement` | The package that replaces this one. |
| `note` | The reason for the state and the required action. |

The fields `disable_date_in_days` and `deprecation_date_in_days` give the number of days from the check date. A negative value means that the date has passed.

### `tap_formulae`

This section records the versions that the tap pins. The `status` field gives the relation to the upstream release.

## Packages that need action now

| Package | State | Action |
|---|---|---|
| `icu4c@79` | active | Keep it. It replaces the disabled `icu4c@76`. |
| `openjdk@21` | disable on 2031-09-30 | Keep it. The main project tests Java 17 to 27. |
| `openssl@3` | disable on 2031-04-08 | Keep it until then. The main project supports 3.5.9. |
| `python@3.12` | disable on 2029-11-01 | Move it to `python@3.15` when the module changes. |
| `php@8.3` | disable on 2028-12-31 | Keep it. The main project supports PHP 8.3 to 8.5. |
| `php@8.4` | disable on 2029-12-31 | Keep it. The main project supports PHP 8.3 to 8.5. |
| `php@8.5` | disable on 2030-12-31 | Keep it. The main project supports PHP 8.3 to 8.5. |

## PHP version coherence

The tap ships one formula per supported PHP series: `php-embed`, `php-embed@8.4`, `php-embed@8.3`, and one `unit-php` module per series.

Each formula pins the homebrew-core php formula of the same series. The pin matters because the php module reads `php-config` from `PATH`. A wrong pin gives the module the headers of another PHP version.

Each module formula passes three arguments to the configure script.

| Argument | Purpose |
|---|---|
| `--config=` | The php-config of the pinned series. |
| `--lib-path=` | The directory with the embed-enabled libphp of the same series. |
| `--module=` | The module name. It gives each series its own object file and its own make target. |

The module names are `php`, `php84`, and `php83`. The module object files are `php.unit.so`, `php84.unit.so`, and `php83.unit.so`. They share one directory, so all three series can run at the same time.

The module type stays `php` in every series. The module exports its own PHP version, so the application config selects a series with the `version` field.

The check script verifies every pin. It fails when a formula builds a different PHP series than it depends on.

```
error: php-embed@8.4.rb: must depend on php@8.4
```

## How to update the file

1. Run the check script.
2. Read the report. It lists every package with its state.
3. If the upstream version changes, update the tap formulae.
4. Commit `eol.json` with the formula change.

```bash
python3 eol/check.py            # print the report, change nothing
python3 eol/check.py --write    # update eol/eol.json
python3 eol/check.py --check    # exit 1 if eol.json is stale
```

The script reads the dependencies from the formulae in `Formula/`. It fetches the live state from the Homebrew formula API. It also fetches the tap versions from the FreeUnit repository and the njs repository.

The script overwrites the machine fields. These fields come from the live data: `current_version`, `deprecated`, `deprecation_date`, `disabled`, `disable_date`, `status`, and the days fields.

The script keeps the human fields. These fields stay as you wrote them: `note`, `replacement`, `source`, and `revision`.

The script needs no GitHub token. It reads the public files with HTTPS.

## What to do when a package is disabled

1. Find the disabled package in `eol.json`.
2. Read the `replacement` field.
3. Change the dependency in the formula listed in `used_by`.
4. Run the tap syntax check.
5. Push the branch and open the pull request.

```bash
brew test-bot --only-tap-syntax
```

The CI build stops at the first failure. One failed package cancels all other jobs in the matrix. Read the job log to find the first error.

```bash
gh pr checks <N> --repo freeunitorg/homebrew-unit
gh api repos/freeunitorg/homebrew-unit/actions/jobs/<job_id>/logs
```

The `gh pr checks` command exits with code 1 when a check fails. This exit code shows the failure. The command itself does not fail.

## Relation to the main project

The FreeUnit repository holds the same data in `pkg/eol.json`. That file records the EOL dates of the operating systems and the runtime versions. This file records the state of the Homebrew packages.

When you plan an update, use both files.
