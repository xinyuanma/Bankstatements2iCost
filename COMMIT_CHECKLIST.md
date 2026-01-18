# What to commit (short checklist)

1. Code & logic

- Add or update files under `src/` only for functional changes.
- Keep `mappings.yaml` under version control; review rules carefully before committing.

2. Project metadata

- Commit `pyproject.toml` and any lockfile (`poetry.lock` or `requirements.txt`).

3. Documentation

- Update `README.md` and any usage examples when behaviour changes.

4. Don't commit

- Do not commit `.venv/`, `.env` with secrets, or site-packages.
- Avoid committing large generated CSVs — keep examples in `samples/` small.

5. Optional checks before pushing

- Run basic lint: `python -m pip install -r requirements-dev.txt && ruff check src` (if you have a linter).
- Run a conversion smoke test:

```bash
bank2csv -i bankstatements/lin-transactions20251215-20260115.csv -o samples/converted_test.csv -m mappings.yaml
```

If the conversion runs and produces rows, it's safe to include the change.
