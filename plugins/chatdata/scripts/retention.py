#!/usr/bin/env python3
"""Dependency-free exact calendar-period retention. Reads CSV; emits aggregates only."""
import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def timestamp(value, label):
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if result.tzinfo is None or result.utcoffset() is None:
            raise ValueError
        return result.astimezone(timezone.utc)
    except (ValueError, TypeError, AttributeError, OverflowError):
        raise ValueError(f'{label} must be an ISO 8601 timestamp with an explicit UTC offset') from None


def rows(path, columns, label):
    with open(path, newline='', encoding='utf-8-sig') as source:
        reader = csv.DictReader(source)
        if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise ValueError(f'{label} CSV needs unique column headers')
        if not set(columns).issubset(reader.fieldnames):
            raise ValueError(f'{label} CSV is missing required columns')
        for row in reader:
            if None in row or any(row.get(column) is None or not row[column].strip() for column in columns):
                raise ValueError(f'{label} CSV contains a malformed row or empty required field')
            yield row


def period_start(instant, frequency, zone):
    day = instant.astimezone(zone).date()
    if frequency == 'week':
        day -= timedelta(days=day.weekday())
    elif frequency == 'month':
        day = day.replace(day=1)
    return day


def shift_period(day, age, frequency):
    if frequency == 'month':
        index = day.year * 12 + day.month - 1 + age
        return day.replace(year=index // 12, month=index % 12 + 1)
    return day + timedelta(days=age * (7 if frequency == 'week' else 1))


def retention(cohorts, activity, *, as_of, timezone_name, frequency='week', periods=12,
              entity_column='entity_id', cohort_column='cohort_at', activity_column='activity_at'):
    """Measure exact-period return activity using an explicit, exclusive data cutoff.

    Cohort CSV must cover all entrants, including entities with no return activity.
    Duplicate entry rows are allowed only when their instants are identical.
    periods is the number of displayed cells, including age zero.
    """
    cutoff = timestamp(as_of, 'as_of')
    try:
        zone = ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, ValueError, TypeError):
        raise ValueError('timezone must be a valid IANA timezone') from None
    if frequency not in ('day', 'week', 'month'):
        raise ValueError('frequency must be day, week, or month')
    if isinstance(periods, bool) or not isinstance(periods, int) or not 1 <= periods <= 1000:
        raise ValueError('periods must be an integer from 1 to 1000')
    if entity_column in (cohort_column, activity_column):
        raise ValueError('entity and timestamp columns must differ')

    entries = {}
    duplicate_entries = 0
    for row in rows(cohorts, [entity_column, cohort_column], 'cohort'):
        entity = row[entity_column]
        entered = timestamp(row[cohort_column], 'cohort_at')
        if entity in entries:
            if entries[entity] != entered:
                raise ValueError('An entity has conflicting cohort entry timestamps; resolve membership before analysis')
            duplicate_entries += 1
        entries[entity] = entered
    if not entries:
        raise ValueError('cohort CSV has no entities')

    eligible = {entity: entered for entity, entered in entries.items() if entered < cutoff}
    sizes = Counter(period_start(entered, frequency, zone) for entered in eligible.values())
    active = defaultdict(set)
    seen = set()
    duplicate_activity = excluded_activity = 0
    for row in rows(activity, [entity_column, activity_column], 'activity'):
        entity = row[entity_column]
        instant = timestamp(row[activity_column], 'activity_at')
        if entity not in entries:
            raise ValueError('Activity contains an entity absent from the cohort CSV')
        if instant < entries[entity]:
            raise ValueError('Activity precedes its entity cohort entry timestamp')
        if instant >= cutoff:
            excluded_activity += 1
            continue
        cohort = period_start(entries[entity], frequency, zone)
        calendar_period = period_start(instant, frequency, zone)
        key = (entity, calendar_period)
        if key in seen:
            duplicate_activity += 1
            continue
        seen.add(key)
        active[(cohort, calendar_period)].add(entity)

    table = []
    for cohort, size in sorted(sizes.items()):
        cells = []
        for age in range(periods):
            start = shift_period(cohort, age, frequency)
            end = shift_period(cohort, age + 1, frequency)
            # Use local calendar boundaries, including 23/25-hour DST days.
            end_instant = datetime.combine(end, datetime.min.time(), zone).astimezone(timezone.utc)
            observed = end_instant <= cutoff
            count = len(active[(cohort, start)]) if observed else None
            cells.append({'age': age, 'period_start': start.isoformat(),
                          'period_end_exclusive': end.isoformat(),
                          'status': 'observed' if observed else 'unobserved',
                          'cohort_size': size, 'retained': count,
                          'rate': count / size if observed else None})
        table.append({'cohort_start': cohort.isoformat(), 'cohort_size': size, 'cells': cells})

    return {'method': 'exact_calendar_period_retention', 'frequency': frequency,
            'timezone': timezone_name, 'as_of_exclusive': cutoff.isoformat(),
            'period_zero': 'Qualifying return activity after entry in the entry calendar period; not automatic enrollment',
            'week_start': 'Monday' if frequency == 'week' else None,
            'checks': {'eligible_entities': len(eligible),
                       'excluded_entities_at_or_after_as_of': len(entries) - len(eligible),
                       'duplicate_cohort_rows': duplicate_entries,
                       'deduplicated_entity_period_activity_rows': duplicate_activity,
                       'excluded_activity_at_or_after_as_of': excluded_activity,
                       'fixed_denominators': True},
            'cohorts': table,
            'limitations': ['Caller must verify complete cohort and qualifying activity coverage through as_of.',
                            'Calendar periods do not represent equal elapsed time since individual entry.',
                            'No rolling retention, churn, survival, revenue retention, or causal estimate is computed.']}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cohorts', required=True, help='CSV containing every cohort entrant, including non-returners')
    parser.add_argument('--activity', required=True, help='CSV containing only qualifying return events')
    parser.add_argument('--as-of', required=True, help='Exclusive complete-data cutoff, with UTC offset')
    parser.add_argument('--timezone', required=True, dest='timezone_name', help='IANA calendar timezone, e.g. America/Los_Angeles')
    parser.add_argument('--frequency', choices=['day', 'week', 'month'], default='week')
    parser.add_argument('--periods', type=int, default=12, help='Number of cells, including age zero (1-1000)')
    parser.add_argument('--entity-column', default='entity_id')
    parser.add_argument('--cohort-column', default='cohort_at')
    parser.add_argument('--activity-column', default='activity_at')
    args = parser.parse_args(argv)
    try:
        result = retention(**vars(args))
    except (ValueError, OSError, UnicodeError, csv.Error, OverflowError):
        # Validation exceptions have controlled messages; filesystem errors can contain private paths.
        error = sys.exc_info()[1]
        message = str(error) if type(error) is ValueError else 'Unable to read inputs or represent requested periods'
        print(json.dumps({'status': 'error', 'error': message}), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
