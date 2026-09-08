#!/usr/bin/env python3
"""Audit equality joins of local CSV extracts without emitting their keys or rows."""
import argparse
from collections import Counter
import csv
from decimal import Decimal, InvalidOperation, localcontext
import json
import sys

RELATIONSHIPS = ('one-to-one', 'one-to-many', 'many-to-one', 'many-to-many')


def read_extract(path, keys, measure=None, null_values=('',)):
    if not keys or len(set(keys)) != len(keys):
        raise ValueError('Key columns must be a nonempty list without duplicates.')
    counts, measures = Counter(), []
    null_rows = rows = 0
    with open(path, newline='', encoding='utf-8-sig') as handle:
        reader = csv.reader(handle, strict=True)
        header = next(reader, None)
        if not header or len(set(header)) != len(header) or any(not name for name in header):
            raise ValueError('CSV must have a nonempty, unique header.')
        if any(key not in header for key in keys) or (measure is not None and measure not in header):
            raise ValueError('A requested column is missing from the CSV header.')
        key_indices = [header.index(key) for key in keys]
        measure_index = header.index(measure) if measure is not None else None
        for row in reader:
            if len(row) != len(header):
                raise ValueError('CSV row width does not match its header.')
            rows += 1
            key = tuple(row[index] for index in key_indices)
            if any(value in null_values for value in key):
                key = None
                null_rows += 1
            else:
                counts[key] += 1
            if measure_index is not None:
                try:
                    value = Decimal(row[measure_index])
                except InvalidOperation:
                    raise ValueError('The measure contains an invalid numeric value.') from None
                if not value.is_finite():
                    raise ValueError('The measure must contain only finite numbers.')
                # Bound exponent/precision to prevent pathological decimal input.
                if len(value.as_tuple().digits) > 1000 or abs(value.as_tuple().exponent) > 1000:
                    raise ValueError('The measure exceeds supported numeric precision.')
                measures.append((key, value))
    return {'counts': counts, 'rows': rows, 'null_rows': null_rows, 'measures': measures}


def _summary(extract, other):
    counts = extract['counts']
    matched = sum(count for key, count in counts.items() if key in other['counts'])
    return {'rows': extract['rows'], 'null_key_rows': extract['null_rows'],
            'distinct_nonnull_keys': len(counts),
            'duplicate_key_groups': sum(count > 1 for count in counts.values()),
            'rows_in_duplicate_keys': sum(count for count in counts.values() if count > 1),
            'excess_duplicate_rows': sum(count - 1 for count in counts.values()),
            'matched_rows': matched, 'unmatched_rows': extract['rows'] - matched}


def audit(left_path, right_path, left_keys, right_keys, relationship,
          left_measure=None, null_values=('',)):
    if relationship not in RELATIONSHIPS:
        raise ValueError('An explicit supported relationship is required.')
    if len(left_keys) != len(right_keys):
        raise ValueError('Left and right key lists must have the same length.')
    left = read_extract(left_path, left_keys, left_measure, null_values)
    right = read_extract(right_path, right_keys, null_values=null_values)
    lc, rc = left['counts'], right['counts']
    shared = lc.keys() & rc.keys()
    inner_rows = sum(lc[key] * rc[key] for key in shared)
    ls, rs = _summary(left, right), _summary(right, left)
    left_rows = inner_rows + ls['unmatched_rows']
    many_many = sum(lc[key] > 1 and rc[key] > 1 for key in shared)
    reasons = []
    if relationship in ('one-to-one', 'one-to-many') and ls['duplicate_key_groups']:
        reasons.append('left_keys_not_unique')
    if relationship in ('one-to-one', 'many-to-one') and rs['duplicate_key_groups']:
        reasons.append('right_keys_not_unique')
    if many_many:
        reasons.append('many_to_many_fanout')
    repeated_left_rows = sum(lc[key] for key in shared if rc[key] > 1)
    result = {'status': 'blocked' if reasons else 'passed', 'blocking_reasons': reasons,
              'scope': 'Provided extracts only; does not validate the full source or arbitrary SQL.',
              'semantics': 'Exact text equality; a NULL in any key component never matches; no trimming or coercion.',
              'expected_relationship': relationship, 'left': ls, 'right': rs,
              'matched_key_groups': len(shared), 'many_to_many_key_groups': many_many,
              'inner_output_rows': inner_rows, 'left_output_rows': left_rows,
              'left_rows_repeated_by_join': repeated_left_rows}
    if left_measure is not None:
        # Input scale is bounded above, and row multiplicity needs at most this many extra digits.
        with localcontext() as context:
            context.prec = 3000 + len(str(max(left['rows'], right['rows'], 1))) * 2
            baseline = matched_baseline = inner_total = left_total = Decimal(0)
            for key, value in left['measures']:
                matches = rc.get(key, 0) if key is not None else 0
                baseline += value
                if matches:
                    matched_baseline += value
                inner_total += value * matches
                left_total += value * max(matches, 1)
            result['left_measure_reconciliation'] = {
                'input_total': str(baseline), 'matched_input_total': str(matched_baseline),
                'inner_output_total': str(inner_total), 'left_output_total': str(left_total),
                'inner_fanout_delta': str(inner_total - matched_baseline),
                'left_fanout_delta': str(left_total - baseline),
                'unmatched_input_total': str(baseline - matched_baseline),
                'numeric_encoding': 'decimal strings'}
        if repeated_left_rows:
            reasons.append('left_measure_repeated_by_join')
            result['status'] = 'blocked'
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--left', required=True)
    parser.add_argument('--right', required=True)
    parser.add_argument('--left-keys', nargs='+', required=True)
    parser.add_argument('--right-keys', nargs='+', required=True)
    parser.add_argument('--relationship', choices=RELATIONSHIPS, required=True)
    parser.add_argument('--left-measure')
    parser.add_argument('--null-value', action='append', default=[],
                        help='Additional exact NULL token; empty fields are always NULL.')
    args = parser.parse_args(argv)
    try:
        result = audit(args.left, args.right, args.left_keys, args.right_keys,
                       args.relationship, args.left_measure, tuple([''] + args.null_value))
    except (OSError, ValueError, csv.Error, UnicodeError):
        # Exceptions can contain source values or paths. Do not emit them.
        print(json.dumps({'status': 'error', 'error': 'Invalid or unreadable input; check CSV structure, columns, keys, and finite numeric measures.'}))
        return 2
    print(json.dumps(result, indent=2, allow_nan=False))
    return 1 if result['status'] == 'blocked' else 0


if __name__ == '__main__':
    sys.exit(main())
