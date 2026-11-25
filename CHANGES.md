# Changelog

## [Unreleased]

### Changed
- Updated formulae to comply with current Homebrew style checks (`brew test-bot --only-tap-syntax`)

### Formula fixes
- **unit.rb**: renamed `post_install` → `post_install_steps` (current Homebrew DSL)
- **unit-ruby.rb**: removed unnecessary string interpolation around `formula_opt_bin("gem")` call
- **php-embed.rb**: replaced `assert_predicate …, :exist?` with `assert_path_exists` in test block
- **unit-wasm.rb**: replaced `assert_predicate …, :exist?` with `assert_path_exists` in test block

### Added
- `.gitignore` for editor artefacts and OS metadata files
- `CHANGES.md` to track formula-level changes
