# Changelog

## [Unreleased]

### Dependencies

- **php-embed.rb**: `icu4c@76` → `icu4c@79`. The `icu4c@76` formula was disabled in homebrew-core on 2026-03-29, so the tap build failed at the dependency step.
- **php-embed.rb**: `php@8.5` → `php`. The formula builds the newest series now, and the unversioned `php` formula of homebrew-core holds it. homebrew-core has no versioned formula for the newest series yet.
- **php-embed.rb**, **php-embed@8.5.rb**, **php-embed@8.4.rb**, **php-embed@8.3.rb**: `zlib` → `zlib-ng-compat` on Linux. The built `libphp` links zlib-ng-compat, and the linkage check fails on an undeclared dependency.
- **unit-java.rb**: `openjdk@11` → `openjdk@21`. The `openjdk@11` formula was deprecated on 2023-09-30. The main project tests the java module with Java 17, 21, 25, 26, and 27.

### New formulae

- **php-embed@8.5.rb**: the PHP 8.5 series, with the patch of the 8.5 source layout.
- **php-embed@8.4.rb**: the PHP 8.4 series, with the patch for the 8.4 source layout.
- **php-embed@8.3.rb**: the PHP 8.3 series, with its own patch. The `PHP_ADD_INCLUDE` macro differs in 8.3, so the 8.4 patch does not apply.
- **unit-php@8.5.rb**: the PHP module for the 8.5 series.
- **unit-php@8.4.rb**: the PHP module for the 8.4 series.
- **unit-php@8.3.rb**: the PHP module for the 8.3 series.

The supported PHP series are 8.3, 8.4, 8.5, and 8.6. The main project lists the same set in `pkg/eol.json` of the `1.37` branch.

### Changed

- **php-embed.rb**: PHP 8.4.28 → 8.6.0.
- **php-embed.rb**: the inreplace patterns of the configure script dropped the line with the flat_namespace flags. PHP 8.6 does not have it, and a pattern that is not in the source fails the build.
- **unit.rb**, **unit-java.rb**, **unit-perl.rb**, **unit-php.rb**, **unit-php@8.3.rb**, **unit-php@8.4.rb**, **unit-php@8.5.rb**, **unit-python3.rb**, **unit-ruby.rb**, **unit-wasm.rb**: the source moved from the tag 1.37.2 to the branch `1.37`, at the commit 56ab4a5baf518b501a1afabc6b1a8c7216805b91. The branch carries the PHP 8.6 support and the 1.37.3 release. The formulae carry the version 1.37.3 and read it from the version file of the branch.
- **unit-php.rb**: the module takes the php-config of the newest series now. The module of the 8.5 series is unit-php@8.5.
- **unit-php.rb**: the module now takes the php-config of its own series with `--config`, and links the embed library of that series with `--lib-path`. Without `--lib-path` the linker does not find an embed-enabled `libphp`, because the homebrew-core php formula does not build the embed SAPI. Without `--config` the module reads the php-config of the unversioned php formula, which tracks the newest PHP release.
- **unit-php@8.5.rb**, **unit-php@8.4.rb**, **unit-php@8.3.rb**: each series gets its own module name (`php85`, `php84`, `php83`), so the object files and the make targets differ. The four series can run at the same time.
- **.github/workflows/main.yml**: added `fail-fast: false` to the build matrix. One failed job no longer cancels the other jobs.
- **.github/workflows/main.yml**: removed `--fail-fast` from `brew test-bot`. Every formula of the job now gets built.
- **.github/workflows/main.yml**: the matrix now builds the versioned php module with the versioned embed library of the same series.
- **.github/workflows/main.yml**: the build step takes the tap name from the formula name. The name of the tap works for the upstream repo and for a fork. The case patterns use the bare name of the formula, because the patterns of bash need it.
- **.github/workflows/manual.yml**: added jobs for the php embed formulae and the versioned php modules.
- **.github/workflows/main.yml**: the job `check-generate` runs on Linux now. The job checks the syntax of the formulae and builds the matrix, and the checks do not depend on the operating system. The pool of the macOS runners is often full, and a job that waits for a runner for 15 minutes is cancelled by GitHub.
- **.github/workflows/main.yml**: the job fails when the test-bot reports a failed step. The test-bot ignores a failed step of a formula without a bottle, so the job was green with a broken build.
- **unit.rb**: the unitctl resource no longer takes the version of the formula. The tool has its own release series, and the assets of the 1.37.3 release are not published yet. The resource uses the last published release, 1.37.2, until the new one appears. The build failed with the code 404 before.
- **Aliases/**: `php-embed@8.5` and `unit-php@8.5` are gone. Every PHP series has its own formula now. `unit@1.37.2` → `unit@1.37.3`.
- **unit.rb**, **unit-java.rb**, **unit-perl.rb**, **unit-php.rb**, **unit-php@8.3.rb**, **unit-php@8.4.rb**, **unit-php@8.5.rb**, **unit-python3.rb**, **unit-ruby.rb**, **unit-wasm.rb**: the build uses the paths of openssl@3 now. The formulae declared openssl@3, but the paths came from the `openssl` formula of homebrew-core, which is the version 4. The server was compiled against the headers of the version 4 and linked the library of the version 3. The whole stack must use one OpenSSL version, like the images of the FreeUnit project do.
- **php-embed.rb**, **php-embed@8.5.rb**, **php-embed@8.4.rb**, **php-embed@8.3.rb**: the curl extension is built on macOS only. The curl of homebrew-core is bound to OpenSSL 4, and PHP is built against OpenSSL 3. The extension is not built on Linux, because a process with two OpenSSL versions is not safe. The build of Linux failed with the message `configure: error: The libcurl check failed.` before.

### Formula fixes

- **php-embed.rb**, **php-embed@8.5.rb**, **php-embed@8.4.rb**, **php-embed@8.3.rb**: `MacOS.sdk_path_if_needed` → `MacOS.sdk_for_formula(self).path`. The first call is disabled in Homebrew 7, and the build failed with `MethodDeprecatedError` on macOS.
- **php-embed.rb**, **php-embed@8.5.rb**, **php-embed@8.4.rb**, **php-embed@8.3.rb**: the build points pkg-config at openssl@3. The openssl@3 formula is keg-only, so pkg-config did not see it and PHP linked the default openssl@4 of homebrew-core. The FreeUnit images build PHP against OpenSSL 3, and the whole process runs on one OpenSSL there.
- **php-embed.rb**: `--with-pic` → `--enable-pic`. The libtool of PHP 8.6 rejects the old option and the build failed at the configure step. The earlier series keep `--with-pic`.
- **unit.rb**: renamed `post_install` → `post_install_steps` (current Homebrew DSL)
- **unit-ruby.rb**: removed unnecessary string interpolation around `formula_opt_bin("gem")` call
- **php-embed.rb**: replaced `assert_predicate …, :exist?` with `assert_path_exists` in test block
- **unit-wasm.rb**: replaced `assert_predicate …, :exist?` with `assert_path_exists` in test block
- **php-embed@8.3.rb**, **php-embed@8.4.rb**: moved the `livecheck` and `head` blocks above `keg_only`. Homebrew checks the order of the formula components.
- **unit-php.rb**, **unit-php@8.4.rb**, **unit-php@8.3.rb**: replaced `Formula["…"].opt_bin` and `Formula["…"].opt_lib` with `formula_opt_bin` and `formula_opt_lib`. The resulting path is the same.
- **php-embed@8.3.rb**: the inreplace patterns of the configure script now use the backticks. PHP changed the quoting of the APXS lines between the series 8.3 and 8.4. The series 8.3 uses backticks, the later series use the `$()` form. The build failed with the message `inreplace failed`.
- **php-embed.rb**, **php-embed@8.4.rb**, **php-embed@8.3.rb**: the `head` block now has the branch name. The audit reported `Git head URL must specify a branch name`.
- **php-embed.rb**, **php-embed@8.4.rb**, **php-embed@8.3.rb**: the livecheck block uses the page `https://www.php.net/downloads?source=Y` and the version of the series. The old page holds no tarball, so the livecheck reported `Unable to get versions`. The old regex also found the versions of the other series.
- **unit-ruby.rb**: the option `--ruby` takes the ruby executable now, not the directory of the binaries. The module of the server runs the program of the option, and the build failed with the message `./configure: error: no Ruby found.` before.
- **php-embed@8.5.rb**: the patch of the source matches the layout of the series 8.5. The context lines of the two hunks of `build/php.m4` and the context line of `configure.ac` were the ones of the other series. The build of macOS failed with the message `1 out of 2 hunks failed` before.

### Added

- `eol/eol.json`: the EOL state of every package the tap depends on
- `eol/check.py`: the script that refreshes `eol.json` and checks the PHP version coherence
- `eol/README.md`: the description of the EOL data and the update procedure
- `test/`: a container that runs the local checks of the tap. It holds Homebrew on Linux.
- `test/README.md`: the description of the local checks
- `test/check-components-order.py`: the check of the formula component order. It needs only Python 3.
- `test/check-inreplace-patterns.py`: the check of the inreplace patterns of the php embed formulae. It reads the configure script of the PHP source of the formula. It needs only Python 3.
- `test/check-patches.py`: the check of the patches of the php embed formulae. It reads the patch from the formula and applies it to the PHP source of the formula in the dry run mode. It needs only Python 3 and the program `patch`.
- `test/run-checks.sh`: the script that runs the local checks. It runs the livecheck of every formula now. The flag `--build` builds a formula and runs the audit of it, like the CI job does.
- `test/entrypoint.sh`: the script that prepares the working copy in the container
- `.gitignore` for editor artefacts and OS metadata files
- `CHANGES.md` to track formula-level changes

### Checks

- `test/run-checks.sh`: the build mode installs the formula with `--build-from-source` now. The option `--build-bottle` fails with the error `UnbottledError` when a dependency has no bottle, and the module formulae depend on the `unit` and the `php-embed` formulae. The CI job installs the formula without the option.
- `test/run-checks.sh`: the build mode unlinks the formulae before the build. The versions of the php embed formulae install the library file with the same name, and only one of them can be linked into the prefix. The CI job builds one formula per runner.
- `test/run-checks.sh`: the build mode checks the keg of the formula when the install fails. The link of the library file fails when another version of the formula is linked into the prefix, and the formula is installed then. A failed build leaves no keg.
- `test/run-checks.sh`: the build mode runs `brew linkage --test` now, like the CI job. The check finds an undeclared dependency without a full CI cycle.
- `eol/check.py`: the mode `--check` reported the file as stale on every run. It compared the date of the check with itself. The day counters change every day, so they did the same.
- `eol/check.py`: the formulae of the tap no longer appear in the list of the packages. The script reads the names from the `Formula` and `Aliases` directories.
- `eol/check.py`: the script retries a request when the Homebrew API answers with the code 503.
- `eol/eol.json`: the versions of `php-embed@8.3` and `php-embed@8.4` are now in the section `tap_formulae`. The section `packages` holds 39 packages.
- `test/run-checks.sh`: the flag `--patch` runs the check of the patches of the php embed formulae. The check finds a patch with the context of the wrong series without a full CI cycle. The program `patch` of macOS refuses such a patch, and the program of Linux applies it with the fuzz.
