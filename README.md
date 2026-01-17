# Bank statements → iCost converter

Small Python utility that converts bank statement CSVs (from `bankstatements/`) into a CSV formatted for import into your bookkeeping software (`samples/converted_example.csv`). The conversion is driven by a YAML rule file so non-developers can adjust categorization and defaults without touching code.

## Features
- Parse semicolon-separated CSV from banks (European decimal commas supported)
- Mapping-driven rules (`mappings.yaml`) for: type inference, category assignment, account defaults, tags, ledger
- Output with Chinese column headers: `日期,类型,金额,一级分类,二级分类,账户1,账户2,备注,货币,标签,账本`

## Quickstart

1. Create a Python 3 virtual environment and install dependencies:

```bash
python3 -m venv ./.venv
source ./.venv/bin/activate
pip install -r requirements.txt
```

2. Place your bank CSV into `bankstatements/` (the repository includes an example file).

3. Edit `mappings.yaml` to adjust rules or defaults. See `mappings.yaml` for current rules and examples.

4. Run the converter:

```bash
./.venv/bin/python3 src/transform_prelim.py
```

5. Output is written to `samples/converted_example.csv`.

## Configuration (`mappings.yaml`)

- `defaults`: keys like `account1`, `currency`, `ledger`, `tag`, `category1`, `category2`.
- `rules`: ordered list of rule objects. Each rule has `name`, `when`, and `actions`.
  - `when` supports `description_equals`, `code_equals`, `amount_exists`, `remark_contains` (list).
  - `actions` supports `infer_type_from_amount: true` and `set` mapping using Chinese output keys (`类型`, `一级分类`, `二级分类`, `账户1`, `账户2`, `备注`, `货币`, `标签`, `账本`).

Rules are applied in file order; later rules override earlier ones when they `set` the same fields.

## Development

- Run formatter / static checks before opening a PR.
- Tests: none currently; recommend running the converter locally against the provided sample file when making changes.

## Contributing

1. Fork the repository and create a feature branch.
2. Make your changes; run the converter to validate behavior.
3. Open a pull request with a clear description of the change and the rationale.

If you're adding or changing mapping semantics, update `mappings.yaml` and include before/after examples of affected rows.

## Troubleshooting

- If mappings do not appear to take effect:
  - Ensure `mappings.yaml` is valid YAML (no duplicate keys in the same mapping).
  - Rules are matched case-insensitively against the `备注` field; ensure your keywords match substrings of that text.
- To debug which rule matched a row, consider temporarily adding rules that set a visible `标签` value for testing.

## License

This repo contains no license header. Add a LICENSE file if you want to make the project public.

---
If you want, I can also:
- add a `--dry-run` flag that prints matched rules per row,
- create a `CONTRIBUTING.md` template,
- commit the README for you.
