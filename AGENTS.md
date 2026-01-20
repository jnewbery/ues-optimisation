This repository contains [Marimo](https://marimo.io/) notebooks.

- When editing Marimo notebooks, always run `uvx marimo check` on the file and fix all issues that you find.
- When adding new python dependencies, make sure to add them to `pyproject.toml` and run `uv lock` to update the lock file.
