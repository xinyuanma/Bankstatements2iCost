#!/usr/bin/env python3
import csv
from pathlib import Path
import yaml
import sys

ROOT = Path(__file__).resolve().parents[1]
IN_FILE = ROOT / 'bankstatements' / 'transactions20251201-20260117.csv'
OUT_DIR = ROOT / 'samples'
OUT_FILE = OUT_DIR / 'converted_example.csv'

OUT_DIR.mkdir(exist_ok=True)

def parse_amount(s: str) -> str:
    if s is None:
        return ''
    s = s.strip().strip('"')
    # European decimal comma to dot
    s = s.replace('.', '')
    s = s.replace(',', '.')
    return s


def load_mappings(path: Path):
    if not path.exists():
        return None
    with path.open('r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def apply_mappings(out: dict, row: dict, mappings: dict):
    if not mappings:
        return out
    # apply defaults
    defaults = mappings.get('defaults', {})
    # If the output fields are empty (''/None), overwrite with defaults from mappings
    if not out.get('F'):
        out['F'] = defaults.get('account1', out.get('F', ''))
    if not out.get('I'):
        out['I'] = defaults.get('currency', out.get('I', 'EUR'))
    if not out.get('K'):
        out['K'] = defaults.get('ledger', out.get('K', '默认账本'))
    if not out.get('J'):
        out['J'] = defaults.get('tag', out.get('J', ''))
    if not out.get('D'):
        out['D'] = defaults.get('category1', out.get('D', ''))
    if not out.get('E'):
        out['E'] = defaults.get('category2', out.get('E', ''))

    rules = mappings.get('rules', [])
    note = (out.get('H') or '')
    note_lower = note.lower()

    # parse amount into numeric for condition checks
    amt_val = None
    try:
        amt_val = float(parse_amount(row.get('Amount EUR', '0')))
    except Exception:
        amt_val = None

    for rule in rules:
        when = rule.get('when', {})
        match = False

        def eval_simple(cond: dict) -> bool:
            # cond is a mapping like {'description_equals': 'DEPOSIT'} or {'remark_contains': ['x']}
            if 'description_equals' in cond:
                return (row.get('Description', '') or '').strip().upper() == cond['description_equals'].strip().upper()
            if 'code_equals' in cond:
                return (row.get('Code', '') or '').strip() == str(cond['code_equals'])
            if cond.get('amount_exists'):
                return (row.get('Amount EUR', '') or '').strip() != ''
            if 'remark_contains' in cond:
                for kw in cond['remark_contains']:
                    if kw.lower() in note_lower:
                        return True
                return False
            # date_between: expect dict with 'start' and 'end' in YYYY-MM-DD
            if 'date_between' in cond:
                dr = cond['date_between']
                start = dr.get('start')
                end = dr.get('end')
                # row date is in out['A'] or fields EntryDate/ValueDate
                date_val = (row.get('EntryDate', '') or row.get('ValueDate', '') or out.get('A', ''))
                try:
                    from datetime import datetime
                    d = datetime.strptime(date_val.split()[0], '%Y-%m-%d').date()
                    s = datetime.strptime(start, '%Y-%m-%d').date() if start else None
                    e = datetime.strptime(end, '%Y-%m-%d').date() if end else None
                    if s and d < s:
                        return False
                    if e and d > e:
                        return False
                    return True
                except Exception:
                    return False
            # date_equals: match a specific YYYY-MM-DD date string
            if 'date_equals' in cond:
                date_val = (row.get('EntryDate', '') or row.get('ValueDate', '') or out.get('A', ''))
                try:
                    from datetime import datetime
                    d = datetime.strptime(date_val.split()[0], '%Y-%m-%d').date()
                    target = datetime.strptime(cond['date_equals'], '%Y-%m-%d').date()
                    return d == target
                except Exception:
                    return False
            # amount sign checks
            if 'amount_negative' in cond:
                if amt_val is None:
                    return False
                return amt_val < 0
            if 'amount_positive' in cond:
                if amt_val is None:
                    return False
                return amt_val > 0
            
            
            # recipient/payer contains
            if 'recipient_contains' in cond:
                recip = (row.get('Recipient/Payer', '') or '')
                if isinstance(cond['recipient_contains'], list):
                    for kw in cond['recipient_contains']:
                        if kw.lower() in recip.lower() or kw.lower() in (out.get('H') or '').lower():
                            return True
                    return False
                else:
                    return cond['recipient_contains'].lower() in recip.lower() or cond['recipient_contains'].lower() in (out.get('H') or '').lower()

            # recipient account number contains: look for any column name containing 'account', 'iban' or 'bban'
            if 'recipient_account_contains' in cond:
                keywords = cond['recipient_account_contains']
                if not isinstance(keywords, list):
                    keywords = [keywords]
                # search likely account columns in row keys
                account_cols = [k for k in row.keys() if k and ('account' in k.lower() or 'iban' in k.lower() or 'bban' in k.lower())]
                for col in account_cols:
                    val = (row.get(col, '') or '')
                    for kw in keywords:
                        if kw.lower() in val.lower():
                            return True
                # fallback: also check Recipient/Payer field
                recip = (row.get('Recipient/Payer', '') or '')
                for kw in keywords:
                    if kw.lower() in recip.lower():
                        return True
                return False
            return False

        # support composite conditions: 'all' or 'any' list of condition dicts
        if 'all' in when:
            conds = when.get('all', [])
            match = all(eval_simple(c) for c in conds)
        elif 'any' in when:
            conds = when.get('any', [])
            match = any(eval_simple(c) for c in conds)
        else:
            # legacy: if multiple simple keys present in when, treat as OR across them
            # Build simple condition dicts for each present key
            simple_conds = []
            if 'description_equals' in when:
                simple_conds.append({'description_equals': when['description_equals']})
            if 'code_equals' in when:
                simple_conds.append({'code_equals': when['code_equals']})
            if when.get('amount_exists'):
                simple_conds.append({'amount_exists': True})
            if 'remark_contains' in when:
                simple_conds.append({'remark_contains': when['remark_contains']})
            if simple_conds:
                match = any(eval_simple(c) for c in simple_conds)
            else:
                # when contains non-standard simple conditions (like date_between);
                # evaluate the whole when dict as a single condition
                match = eval_simple(when)

        if match:
            # Special-case: enforce that the 'vacation-mode' rule only applies to expenses (negative amounts).
            # The user requested this logic live in the script rather than encoded in mappings.yaml.
            rule_name = rule.get('name', '')
            if rule_name == 'vacation-mode':
                if amt_val is None or amt_val >= 0:
                    # skip applying this rule for non-expenses
                    continue
            actions = rule.get('actions', {})
            # infer type from amount
            if actions.get('infer_type_from_amount') and out.get('B', '') == '':
                try:
                    amt = float(parse_amount(row.get('Amount EUR', '0')))
                    out['B'] = '支出' if amt < 0 else '收入'
                except Exception:
                    pass
            # set fields (always override existing values when provided)
            set_fields = actions.get('set', {})
            for k, v in set_fields.items():
                # map Chinese keys to out keys
                if k == '类型':
                    out['B'] = v
                elif k == '一级分类':
                    out['D'] = v
                elif k == '二级分类':
                    out['E'] = v
                elif k == '账户1':
                    out['F'] = v
                elif k == '账户2':
                    out['G'] = v
                elif k == '备注':
                    out['H'] = v
                elif k == '货币':
                    out['I'] = v
                elif k == '标签':
                    out['J'] = v
                elif k == '账本':
                    out['K'] = v
    return out

def transform_row(row: dict, mappings: dict = None) -> dict:
    # Input fields based on the sample CSV header
    entry_date = row.get('EntryDate', '') or row.get('ValueDate', '')
    code = row.get('Code', '').strip('"')
    desc = row.get('Description', '').strip('"')
    recipient = row.get('Recipient/Payer', '').strip('"')
    amount_raw = row.get('Amount EUR', '')
    amount = parse_amount(amount_raw)
    reference = row.get('Reference', '')
    message = row.get('Message', '')

    # Parse numeric amount; do not set 类型 here — let mappings.yaml rules decide
    try:
        amt_val = float(amount)
    except Exception:
        amt_val = None

    # After determining type, convert amount to absolute value string
    if amt_val is not None:
        amount_abs = f"{abs(amt_val):.2f}"
    else:
        # fallback to original parsed string
        amount_abs = amount

    out = {
        'A': entry_date,
        'B': '',
        'C': amount_abs,
        'D': '',
        'E': '',
        'F': '',
        'G': '',
        'H': recipient,
        'I': 'EUR',
        'J': '',
        'K': '默认账本',
    }

    # Apply mappings from mappings.yaml (if provided) which can override fields
    if mappings:
        out = apply_mappings(out, row, mappings)

    # Defaults (managed in mappings.yaml.defaults). No hard-coded type/account fallbacks here.

    # Category mapping is driven by mappings.yaml rules now.
    # All category rules should be defined in mappings.yaml so non-developers can edit them.

    return out

def main():
    with IN_FILE.open('r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';', quotechar='"')
        raw_rows = list(reader)

    # Clean header names and values: strip whitespace and surrounding quotes
    rows = []
    for r in raw_rows:
        clean = {}
        for k, v in r.items():
            if k is None:
                continue
            key = k.strip().strip('"')
            if isinstance(v, str):
                val = v.strip().strip('"')
            else:
                val = v
            clean[key] = val
        rows.append(clean)

    mappings = load_mappings(ROOT / 'mappings.yaml')
    transformed = [transform_row(r, mappings) for r in rows]

    # Map A-K to the requested Chinese column names:
    chinese_fields = [
        '日期',  # A
        '类型',  # B
        '金额',  # C
        '一级分类',  # D
        '二级分类',  # E
        '账户1',  # F
        '账户2',  # G
        '备注',  # H
        '货币',  # I
        '标签',  # J
        '账本',  # K
    ]

    with OUT_FILE.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=chinese_fields)
        writer.writeheader()
        for r in transformed:
            row = {
                '日期': r.get('A', ''),
                '类型': r.get('B', ''),
                '金额': r.get('C', ''),
                '一级分类': r.get('D', ''),
                '二级分类': r.get('E', ''),
                '账户1': r.get('F', ''),
                '账户2': r.get('G', ''),
                '备注': r.get('H', ''),
                '货币': r.get('I', ''),
                '标签': r.get('J', ''),
                '账本': r.get('K', ''),
            }
            writer.writerow(row)

    print(f'Wrote {len(transformed)} rows to {OUT_FILE}')

if __name__ == '__main__':
    main()
