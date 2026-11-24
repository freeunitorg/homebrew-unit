# FreeUnit Homebrew tap

The official Homebrew tap of [FreeUnit](https://freeunit.org), the
community fork of NGINX Unit. FreeUnit is a lightweight, dynamic,
open-source web and application server.

The formulas track the released FreeUnit versions. The tap is community
maintained.

## Install

Tap the repository, then install the server:

```console
$ brew tap freeunitorg/unit https://github.com/freeunitorg/homebrew-unit
$ brew install freeunitorg/unit/unit
```

Or install a formula by its full name:

```console
$ brew install freeunitorg/unit/unit-php
```

## Formulae

| Formula | What it gives |
| ------- | ------------- |
| `unit` | The `unitd` server with njs, plus the released `unitctl` binary |
| `unit-php` | PHP module (needs `php-embed`) |
| `unit-python3` | Python 3 module |
| `unit-java` | Java module |
| `unit-perl` | Perl module |
| `unit-ruby` | Ruby module |
| `unit-wasm` | WebAssembly module |
| `php-embed` | PHP built with the embed SAPI |

## Notes

- The `unit` formula installs the `unitctl` binary published with the
  matching [release](https://github.com/freeunitorg/freeunit/releases),
  and installs njs as `njs-unit`.
- The module formulae build against the `unit` release of the same
  version and install the module into `lib/unit/modules`.
- For Python, install `unit-python3`. The `unit-python` formula is the
  old Python 2 module. Apple removed Python 2 from macOS. The formula
  refuses macOS versions newer than Big Sur. It cannot build on a
  system that Homebrew supports.
- The tap CI runs `brew test-bot` on pull requests and rebuilds
  everything weekly.

## Versioned aliases

- `unit@1.37.2` — pin of the current release
- `php-embed@8.4` — pin of the PHP 8.4 series

## Links

- Documentation: https://docs.freeunit.org
- Source: https://github.com/freeunitorg/freeunit
- Discussions: https://github.com/freeunitorg/freeunit/discussions

`brew help`, `man brew`, or the
[Homebrew documentation](https://docs.brew.sh) cover Homebrew itself.
