import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / 'plugins/chatdata/scripts/retention.py'
spec = importlib.util.spec_from_file_location('retention', SCRIPT)
R = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R)


class RetentionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.cohorts = Path(self.temp.name) / 'cohorts.csv'
        self.activity = Path(self.temp.name) / 'activity.csv'
        self.cohorts.write_text('entity_id,cohort_at\na,2026-01-01T00:00:00Z\nb,2026-01-01T12:00:00Z\n')
        self.activity.write_text('entity_id,activity_at\na,2026-01-02T01:00:00Z\na,2026-01-02T23:00:00Z\n')

    def run_check(self, **kwargs):
        options = dict(as_of='2026-01-04T00:00:00Z', timezone_name='UTC', frequency='day', periods=4)
        options.update(kwargs)
        return R.retention(self.cohorts, self.activity, **options)

    def test_full_denominator_deduplication_and_zero_vs_unobserved(self):
        result = self.run_check()
        cells = result['cohorts'][0]['cells']
        self.assertEqual([c['retained'] for c in cells], [0, 1, 0, None])
        self.assertEqual([c['rate'] for c in cells], [0, .5, 0, None])
        self.assertEqual([c['cohort_size'] for c in cells], [2] * 4)
        self.assertEqual(cells[3]['status'], 'unobserved')
        self.assertEqual(result['checks']['deduplicated_entity_period_activity_rows'], 1)

    def test_partial_period_masks_activity_already_seen(self):
        cells = self.run_check(as_of='2026-01-02T12:00:00Z')['cohorts'][0]['cells']
        self.assertIsNone(cells[1]['retained'])
        self.assertIsNone(cells[1]['rate'])

    def test_exact_cutoff_excludes_events_and_entrants(self):
        self.cohorts.write_text('entity_id,cohort_at\na,2026-01-01T00:00:00Z\nb,2026-01-02T00:00:00Z\n')
        self.activity.write_text('entity_id,activity_at\na,2026-01-02T00:00:00Z\nb,2026-01-02T00:00:00Z\n')
        result = self.run_check(as_of='2026-01-02T00:00:00Z')
        self.assertEqual(result['checks']['eligible_entities'], 1)
        self.assertEqual(result['checks']['excluded_entities_at_or_after_as_of'], 1)
        self.assertEqual(result['checks']['excluded_activity_at_or_after_as_of'], 2)
        self.assertEqual(len(result['cohorts']), 1)

    def test_conflicting_membership_is_rejected(self):
        with self.cohorts.open('a') as file:
            file.write('a,2026-01-02T00:00:00Z\n')
        with self.assertRaisesRegex(ValueError, 'conflicting'):
            self.run_check()

    def test_same_instant_duplicate_membership_does_not_inflate(self):
        with self.cohorts.open('a') as file:
            file.write('a,2025-12-31T16:00:00-08:00\n')
        result = self.run_check()
        self.assertEqual(result['checks']['duplicate_cohort_rows'], 1)
        self.assertEqual(result['cohorts'][0]['cohort_size'], 2)

    def test_activity_before_entry_rejected_even_in_same_calendar_period(self):
        self.activity.write_text('entity_id,activity_at\nb,2026-01-01T11:59:59Z\n')
        with self.assertRaisesRegex(ValueError, 'precedes'):
            self.run_check()

    def test_unknown_activity_entity_rejected(self):
        self.activity.write_text('entity_id,activity_at\nsecret@example.com,2026-01-02T00:00:00Z\n')
        with self.assertRaisesRegex(ValueError, 'absent') as error:
            self.run_check()
        self.assertNotIn('secret', str(error.exception))

    def test_naive_timestamps_rejected_in_all_sources(self):
        original_cohorts = self.cohorts.read_text()
        original_activity = self.activity.read_text()
        for field in ('as_of', 'cohort', 'activity'):
            with self.subTest(field=field):
                self.cohorts.write_text(original_cohorts)
                self.activity.write_text(original_activity)
                options = {}
                if field == 'as_of':
                    options['as_of'] = '2026-01-04T00:00:00'
                else:
                    path = self.cohorts if field == 'cohort' else self.activity
                    path.write_text(path.read_text().replace('Z', ''))
                with self.assertRaisesRegex(ValueError, 'explicit UTC offset'):
                    self.run_check(**options)

    def test_cohort_age_is_separate_from_calendar_date(self):
        self.cohorts.write_text('entity_id,cohort_at\na,2026-01-01T00:00:00Z\nb,2026-01-02T00:00:00Z\nc,2026-01-02T01:00:00Z\n')
        self.activity.write_text('entity_id,activity_at\na,2026-01-02T00:00:00Z\nb,2026-01-03T00:00:00Z\n')
        cohorts = self.run_check()['cohorts']
        self.assertEqual([c['cohort_size'] for c in cohorts], [1, 2])
        self.assertEqual([c['rate'] for c in cohorts[0]['cells']], [0, 1, 0, None])
        self.assertEqual([c['rate'] for c in cohorts[1]['cells']], [0, .5, None, None])

    def test_timezone_changes_cohort_calendar_date(self):
        result = self.run_check(timezone_name='America/Los_Angeles')
        self.assertEqual([c['cohort_start'] for c in result['cohorts']], ['2025-12-31', '2026-01-01'])

    def test_dst_spring_day_is_mature_after_23_hours(self):
        self.cohorts.write_text('entity_id,cohort_at\na,2026-03-08T00:00:00-08:00\n')
        self.activity.write_text('entity_id,activity_at\na,2026-03-08T23:00:00-07:00\n')
        result = self.run_check(as_of='2026-03-09T00:00:00-07:00', timezone_name='America/Los_Angeles')
        self.assertEqual(result['cohorts'][0]['cells'][0]['rate'], 1)
        self.assertIsNone(result['cohorts'][0]['cells'][1]['rate'])

    def test_dst_fall_day_needs_25_hours(self):
        self.cohorts.write_text('entity_id,cohort_at\na,2026-11-01T00:00:00-07:00\n')
        self.activity.write_text('entity_id,activity_at\na,2026-11-01T01:30:00-07:00\na,2026-11-01T01:30:00-08:00\n')
        result = self.run_check(as_of='2026-11-01T23:00:00-08:00', timezone_name='America/Los_Angeles')
        self.assertIsNone(result['cohorts'][0]['cells'][0]['rate'])
        result = self.run_check(as_of='2026-11-02T00:00:00-08:00', timezone_name='America/Los_Angeles')
        self.assertEqual(result['cohorts'][0]['cells'][0]['retained'], 1)

    def test_week_starts_monday_and_crosses_year(self):
        result = self.run_check(frequency='week', as_of='2026-01-05T00:00:00Z')
        self.assertEqual(result['cohorts'][0]['cohort_start'], '2025-12-29')
        self.assertEqual(result['cohorts'][0]['cells'][0]['rate'], .5)
        self.assertIsNone(result['cohorts'][0]['cells'][1]['rate'])

    def test_months_handle_leap_year_and_variable_lengths(self):
        self.cohorts.write_text('entity_id,cohort_at\na,2024-01-31T00:00:00Z\n')
        self.activity.write_text('entity_id,activity_at\na,2024-02-29T23:59:59Z\n')
        cells = self.run_check(frequency='month', as_of='2024-03-01T00:00:00Z')['cohorts'][0]['cells']
        self.assertEqual([c['retained'] for c in cells], [0, 1, None, None])
        self.assertEqual(cells[1]['period_end_exclusive'], '2024-03-01')

    def test_empty_activity_is_valid_but_empty_cohort_is_not(self):
        self.activity.write_text('entity_id,activity_at\n')
        self.assertEqual(self.run_check()['cohorts'][0]['cells'][1]['retained'], 0)
        self.cohorts.write_text('entity_id,cohort_at\n')
        with self.assertRaisesRegex(ValueError, 'no entities'):
            self.run_check()

    def test_bad_csv_and_invalid_options(self):
        for content in ('entity_id,cohort_at\n,2026-01-01T00:00:00Z\n',
                        'entity_id,cohort_at\na\n',
                        'entity_id,cohort_at\na,2026-01-01T00:00:00Z,extra\n',
                        'entity_id,entity_id\na,b\n', 'wrong,headers\na,b\n'):
            self.cohorts.write_text(content)
            with self.assertRaises(ValueError):
                self.run_check()
        for options in ({'periods': 0}, {'periods': True}, {'periods': 1001},
                        {'timezone_name': 'Not/AZone'}, {'frequency': 'rolling'},
                        {'entity_column': 'cohort_at'}):
            with self.assertRaises(ValueError):
                self.run_check(**options)

    def test_custom_columns(self):
        self.cohorts.write_text('customer,joined\nx,2026-01-01T00:00:00Z\n')
        self.activity.write_text('customer,returned\nx,2026-01-02T00:00:00Z\n')
        result = self.run_check(entity_column='customer', cohort_column='joined', activity_column='returned')
        self.assertEqual(result['cohorts'][0]['cells'][1]['rate'], 1)

    def test_cli_json_and_no_raw_identity_or_paths(self):
        self.cohorts.write_text('entity_id,cohort_at\nprivate-person@example.com,2026-01-01T00:00:00Z\n')
        self.activity.write_text('entity_id,activity_at\nprivate-person@example.com,2026-01-02T00:00:00Z\n')
        command = [sys.executable, str(SCRIPT), '--cohorts', str(self.cohorts), '--activity', str(self.activity),
                   '--as-of', '2026-01-04T00:00:00Z', '--timezone', 'UTC', '--frequency', 'day', '--periods', '4']
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['checks']['eligible_entities'], 1)
        self.assertNotIn('private-person', result.stdout)
        self.assertNotIn(self.temp.name, result.stdout)
        self.cohorts.unlink()
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stderr)['status'], 'error')
        self.assertNotIn(self.temp.name, result.stderr)


if __name__ == '__main__':
    unittest.main()
