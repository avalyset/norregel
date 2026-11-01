# Contributing

Questions, error reports and suggestions are welcome as [Issues](https://github.com/avalyset/norregel/issues).

- **Errors in the scorer, the analysis or the documentation:** open an issue with the file, the line and what you
  expected. A pull request with a test is welcome.
- **Locked files:** files listed in a lock (`LOCK_MANIFEST.md`, `borealis/LAAST_SHA256.json`) or deposited with a
  preregistration are not changed. A fix to one of them goes into a new version with its own record, and the old
  version stays as it is.
- **Items:** the item files are closed. Do not post item texts, answer keys or model answers to them in issues or pull
  requests.
- **Tests:** run `python -m pytest -q -rs` before a pull request. Tests that need the closed items are skipped.

By contributing you agree that code contributions are licensed under the MIT licence (`LICENSE`) and documentation
contributions under CC BY 4.0 (`LICENSE-docs`).
