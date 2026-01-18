import os
from pathlib import Path
import click
from dotenv import load_dotenv

# import transform_file from project module
try:
    from transform_prelim import transform_file as _transform_file
except Exception:
    # last resort: relative import
    from . import transform_file as _transform_file


@click.command()
@click.option('-i', '--input', 'input_path', help='Input CSV file (overrides .env IN_FILE)')
@click.option('-o', '--output', 'output_path', help='Output CSV file (overrides .env OUT_FILE)')
@click.option('-m', '--mappings', 'mappings_path', help='Mappings YAML (overrides .env MAPPINGS)')
@click.option('--default-account1', help='Override default account1 (overrides .env DEFAULT_ACCOUNT1)')
@click.option('--default-currency', help='Override default currency (overrides .env DEFAULT_CURRENCY)')
@click.option('--no-dotenv', is_flag=True, default=False, help='Do not load .env file from cwd')
def cli(input_path, output_path, mappings_path, default_account1, default_currency, no_dotenv):
    """Bank statements -> bookkeeping CSV converter CLI."""
    if not no_dotenv:
        load_dotenv()

    root = Path(os.getcwd())
    in_path = Path(input_path or os.getenv('IN_FILE') or (root / 'bankstatements' / 'transactions20251201-20260117.csv'))
    out_path = Path(output_path or os.getenv('OUT_FILE') or (root / 'samples' / 'converted_example.csv'))
    maps = Path(mappings_path or os.getenv('MAPPINGS') or (root / 'mappings.yaml'))

    # collect default overrides from env or CLI flags
    defaults_override = {
        'account1': os.getenv('DEFAULT_ACCOUNT1'),
        'currency': os.getenv('DEFAULT_CURRENCY'),
    }

    # CLI flags override env
    if default_account1:
        defaults_override['account1'] = default_account1
    if default_currency:
        defaults_override['currency'] = default_currency

    _transform_file(in_path, out_path, maps, defaults_override=defaults_override)

if __name__ == '__main__':
    cli()
