import csv
import importlib.util
import json
import itertools
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'plugins/chatdata/scripts/join_audit.py'
spec = importlib.util.spec_from_file_location('join_audit', SCRIPT)
J = importlib.util.module_from_spec(spec)
spec.loader.exec_module(J)


class JoinAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.left = Path(self.temp.name) / 'left.csv'
        self.right = Path(self.temp.name) / 'right.csv'

    def write(self, left, right):
        for path, rows in [(self.left, left), (self.right, right)]:
            with path.open('w', newline='') as handle:
                csv.writer(handle).writerows(rows)

    def run_audit(self, relationship='many-to-one', **kwargs):
        return J.audit(self.left, self.right, ['id'], ['id'], relationship, **kwargs)

    def test_unique_join_and_unmatched_nulls(self):
        self.write([['id', 'v'], ['a', '1'], ['b', '2'], ['', '3']],
                   [['id'], ['a'], ['c'], ['']])
        r = self.run_audit('one-to-one', left_measure='v')
        self.assertEqual(r['status'], 'passed')
        self.assertEqual((r['inner_output_rows'], r['left_output_rows']), (1, 3))
        self.assertEqual(r['left']['unmatched_rows'], 2)
        self.assertEqual(r['right']['unmatched_rows'], 2)
        self.assertEqual(r['left']['null_key_rows'], 1)
        self.assertEqual(r['left_measure_reconciliation']['left_output_total'], '6')

    def test_many_to_many_exact_counts_and_inflation(self):
        self.write([['id', 'v'], ['secret', '0.1'], ['secret', '0.2'], ['x', '5']],
                   [['id'], ['secret'], ['secret'], ['secret']])
        r = self.run_audit('many-to-many', left_measure='v')
        self.assertEqual((r['inner_output_rows'], r['left_output_rows']), (6, 7))
        self.assertEqual(r['many_to_many_key_groups'], 1)
        self.assertIn('many_to_many_fanout', r['blocking_reasons'])
        self.assertEqual(r['left_measure_reconciliation']['left_fanout_delta'], '0.6')
        self.assertNotIn('secret', json.dumps(r))
        self.assertEqual(r['left']['excess_duplicate_rows'], 1)
        self.assertEqual(r['right']['rows_in_duplicate_keys'], 3)

    def test_each_cardinality_contract(self):
        self.write([['id'], ['a'], ['a']], [['id'], ['a']])
        for relationship in ['one-to-one', 'one-to-many']:
            self.assertIn('left_keys_not_unique', self.run_audit(relationship)['blocking_reasons'])
        self.assertEqual(self.run_audit()['status'], 'passed')
        self.write([['id'], ['a']], [['id'], ['a'], ['a']])
        self.assertEqual(self.run_audit('one-to-many')['status'], 'passed')
        self.assertIn('right_keys_not_unique', self.run_audit()['blocking_reasons'])

    def test_unmatched_duplicates_still_violate_contract(self):
        self.write([['id'], ['a']], [['id'], ['b'], ['b']])
        self.assertEqual(self.run_audit()['status'], 'blocked')

    def test_canceling_measures_cannot_hide_fanout(self):
        self.write([['id', 'v'], ['a', '1'], ['b', '-1']],
                   [['id'], ['a'], ['a'], ['b'], ['b']])
        r = self.run_audit('one-to-many', left_measure='v')
        self.assertEqual(r['left_measure_reconciliation']['left_fanout_delta'], '0')
        self.assertIn('left_measure_repeated_by_join', r['blocking_reasons'])

    def test_composite_keys_and_partial_null(self):
        self.write([['id', 'part'], ['a', '1'], ['a', '2'], ['a', '']],
                   [['other', 'part'], ['a', '1'], ['a', '']])
        r = J.audit(self.left, self.right, ['id', 'part'], ['other', 'part'], 'one-to-one')
        self.assertEqual(r['inner_output_rows'], 1)
        self.assertEqual(r['left']['null_key_rows'], 1)
        self.assertEqual(r['left']['duplicate_key_groups'], 0)

    def test_key_text_is_not_coerced_or_trimmed(self):
        self.write([['id'], ['01'], [' a'], ['NULL']], [['id'], ['1'], ['a'], ['NULL']])
        self.assertEqual(self.run_audit()['inner_output_rows'], 1)
        self.assertEqual(self.run_audit(null_values=('', 'NULL'))['inner_output_rows'], 0)

    def test_empty_extracts_and_repeated_nulls(self):
        self.write([['id']], [['id'], [''], ['']])
        r = self.run_audit('one-to-one')
        self.assertEqual(r['status'], 'passed')
        self.assertEqual(r['left_output_rows'], 0)
        self.assertEqual(r['right']['null_key_rows'], 2)
        self.assertEqual(r['right']['duplicate_key_groups'], 0)

    def test_invalid_schema_and_keys(self):
        for rows in [[['id', 'id']], [['id'], ['a', 'extra']], [['other'], ['a']], []]:
            self.write(rows, [['id']])
            with self.assertRaises(ValueError):
                self.run_audit()
        self.write([['id']], [['id']])
        for keys in [[], ['id', 'id']]:
            with self.assertRaises(ValueError):
                J.audit(self.left, self.right, keys, keys, 'one-to-one')
        with self.assertRaises(ValueError):
            J.audit(self.left, self.right, ['id'], [], 'one-to-one')
        with self.assertRaises(ValueError):
            self.run_audit('guess')

    def test_bad_measures_rejected(self):
        for value in ['', 'NULL', 'nan', 'Infinity', 'private-value', '1e1001']:
            self.write([['id', 'v'], ['a', value]], [['id'], ['a']])
            with self.assertRaises(ValueError):
                self.run_audit(left_measure='v')

    def test_decimal_reconciliation_does_not_round(self):
        self.write([['id', 'v'], ['a', '10000000000000000000000000000.1'], ['b', '0.2']],
                   [['id'], ['a'], ['b']])
        total = self.run_audit(left_measure='v')['left_measure_reconciliation']['input_total']
        self.assertEqual(total, '10000000000000000000000000000.3')

    def test_row_estimates_match_materialized_join(self):
        # Independently enumerate pairs, including duplicate and NULL keys.
        extracts = list(itertools.product(['a', 'b', ''], repeat=2))
        for left in extracts:
            for right in extracts:
                self.write([['id']] + [[x] for x in left],
                           [['id']] + [[x] for x in right])
                pairs = [(l, r) for l in left for r in right if l and r and l == r]
                unmatched = [l for l in left if not any(l and r and l == r for r in right)]
                result = self.run_audit('many-to-many')
                self.assertEqual(result['inner_output_rows'], len(pairs))
                self.assertEqual(result['left_output_rows'], len(pairs) + len(unmatched))

    def test_cli_exit_codes_and_private_error(self):
        args = [sys.executable, str(SCRIPT), '--left', str(self.left), '--right', str(self.right),
                '--left-keys', 'id', '--right-keys', 'id', '--relationship', 'many-to-one']
        self.write([['id', 'v'], ['private-key', 'private-number']], [['id'], ['private-key']])
        passed = subprocess.run(args, capture_output=True, text=True)
        self.assertEqual(passed.returncode, 0)
        self.assertEqual(json.loads(passed.stdout)['status'], 'passed')
        invalid = subprocess.run(args + ['--left-measure', 'v'], capture_output=True, text=True)
        self.assertEqual(invalid.returncode, 2)
        self.assertNotIn('private-', invalid.stdout + invalid.stderr)
        self.write([['id'], ['a']], [['id'], ['a'], ['a']])
        blocked = subprocess.run(args, capture_output=True, text=True)
        self.assertEqual(blocked.returncode, 1)
        self.assertEqual(json.loads(blocked.stdout)['status'], 'blocked')


if __name__ == '__main__':
    unittest.main()
