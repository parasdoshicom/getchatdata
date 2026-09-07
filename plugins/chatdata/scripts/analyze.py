#!/usr/bin/env python3
"""Small, dependency-free analysis checks. No network access or source-data writes."""
import argparse
import csv
import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from statistics import NormalDist


def integer(value, name, positive=False):
    if isinstance(value, bool):
        raise ValueError(f'{name} must be an integer')
    try:
        number = int(value)
    except (ValueError, TypeError, OverflowError):
        raise ValueError(f'{name} must be an integer') from None
    if str(number) != str(value) or number < (1 if positive else 0):
        raise ValueError(f'{name} must be an integer >= {1 if positive else 0}')
    return number


def fraction(value, name):
    number = float(value)
    if not math.isfinite(number) or not 0 < number < 1:
        raise ValueError(f'{name} must be strictly between 0 and 1')
    return number


def wilson(successes, n, alpha=0.05):
    z = NormalDist().inv_cdf(1 - alpha / 2)
    p = successes / n
    center = (p + z*z/(2*n)) / (1 + z*z/n)
    half = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / (1 + z*z/n)
    return [max(0.0, center-half), min(1.0, center+half)]


def experiment(control_n, control_success, treatment_n, treatment_success,
               allocation=0.5, alpha=0.05, min_effect=0.0):
    n0, n1 = integer(control_n, 'control_n', True), integer(treatment_n, 'treatment_n', True)
    x0, x1 = integer(control_success, 'control_success'), integer(treatment_success, 'treatment_success')
    if x0 > n0 or x1 > n1:
        raise ValueError('Successes cannot exceed assigned sample size')
    allocation, alpha = fraction(allocation, 'allocation'), fraction(alpha, 'alpha')
    min_effect = float(min_effect)
    if not math.isfinite(min_effect) or not 0 <= min_effect < 1:
        raise ValueError('min_effect must be an absolute rate difference in [0, 1)')
    expected0, expected1 = (n0+n1)*(1-allocation), (n0+n1)*allocation
    srm_chi = (n0-expected0)**2/expected0 + (n1-expected1)**2/expected1
    srm_p = math.erfc(math.sqrt(srm_chi/2)) if min(expected0, expected1) >= 5 else None
    p0, p1 = x0/n0, x1/n1
    l0, u0 = wilson(x0, n0, alpha)
    l1, u1 = wilson(x1, n1, alpha)
    diff = p1-p0
    interval = [diff-math.hypot(p1-l1, u0-p0), diff+math.hypot(u1-p1, p0-l0)]
    sparse = min(x0, n0-x0, x1, n1-x1) < 5
    pooled = (x0+x1)/(n0+n1)
    se = math.sqrt(pooled*(1-pooled)*(1/n0+1/n1))
    pvalue = math.erfc(abs(diff/se)/math.sqrt(2)) if se and not sparse else None
    if srm_p is None:
        result = 'insufficient_assignment_counts'
    elif srm_p < 0.001:
        result = 'blocked_srm'
    elif sparse:
        result = 'sparse_data_review_required'
    elif interval[0] > min_effect:
        result = 'benefit_candidate_pending_design_and_guardrails'
    elif interval[1] < 0:
        result = 'harm_candidate_pending_design_review'
    else:
        result = 'inconclusive_for_minimum_effect'
    return {'control':{'n':n0,'successes':x0,'rate':p0},'treatment':{'n':n1,'successes':x1,'rate':p1},
            'absolute_difference':diff,'percentage_point_difference':100*diff,
            'relative_lift':diff/p0 if p0 else None,'confidence_level':1-alpha,
            'difference_interval':interval,'interval_method':'Newcombe difference using Wilson score intervals',
            'two_sided_p_value':pvalue,'p_value_method':'pooled two-proportion normal approximation; absent for sparse counts',
            'srm_p_value':srm_p,'srm_threshold':0.001,'planned_treatment_allocation':allocation,
            'minimum_absolute_effect':min_effect,'result':result,
            'limitations':['Independent units, binary outcomes, fixed horizon, one prespecified comparison assumed.',
                           'Assignment/exposure logging, maturity, missingness, multiplicity and guardrails need separate review.',
                           'This result does not authorize launching or shipping an experiment.']}


def power(baseline, absolute_effect, alpha=0.05, target_power=0.8):
    p0, a, target_power = fraction(baseline, 'baseline'), fraction(alpha,'alpha'), fraction(target_power,'power')
    delta = float(absolute_effect)
    if not math.isfinite(delta) or delta == 0 or not 0 < p0+delta < 1:
        raise ValueError('Effect must be nonzero and baseline + effect must lie strictly between 0 and 1')
    if target_power <= 0.5:
        raise ValueError('power must be greater than 0.5')
    p1 = p0+delta
    mean = (p0+p1)/2
    za, zb = NormalDist().inv_cdf(1-a/2), NormalDist().inv_cdf(target_power)
    n = math.ceil((za*math.sqrt(2*mean*(1-mean))+zb*math.sqrt(p0*(1-p0)+p1*(1-p1)))**2/delta**2)
    return {'per_arm':n,'total':2*n,'baseline':p0,'treatment_rate':p1,'absolute_effect':delta,
            'alpha':a,'power':target_power,'method':'two-sided normal approximation, equal allocation, independent binary units',
            'limitations':['No allowance for clustering, attrition, sequential looks, or multiple comparisons.',
                           'Calendar duration must also cover outcome maturity and business cycles.']}


def rows(path):
    with open(path, newline='', encoding='utf-8-sig') as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames) or any(not x for x in reader.fieldnames):
            raise ValueError('CSV must have unique, nonempty column names')
        data = list(reader)
        if any(None in row or any(v is None for v in row.values()) for row in data):
            raise ValueError('CSV contains rows with missing or extra fields')
        return reader.fieldnames, data


def timestamp(value):
    try:
        dt = datetime.fromisoformat(value.replace('Z','+00:00'))
    except (ValueError, AttributeError):
        raise ValueError('Timestamps must be ISO-8601 with an explicit timezone') from None
    if dt.tzinfo is None:
        raise ValueError('Timestamps must include a timezone')
    return dt


def funnel(data, steps, as_of, window_hours=168):
    if len(steps) < 2 or len(set(steps)) != len(steps) or any(not s for s in steps):
        raise ValueError('Provide at least two distinct ordered steps')
    hours = float(window_hours)
    if not math.isfinite(hours) or hours <= 0:
        raise ValueError('window_hours must be finite and positive')
    cutoff, horizon = timestamp(as_of), timedelta(hours=hours)
    groups = defaultdict(list)
    duplicate_count, seen, future = 0, set(), 0
    for row in data:
        if not all(row.get(k,'').strip() for k in ['user_id','event','timestamp']):
            raise ValueError('Each event needs user_id, event, and timestamp')
        time = timestamp(row['timestamp'])
        if time > cutoff:
            future += 1
            continue
        key = (row['user_id'], row['event'], time)
        if key in seen:
            duplicate_count += 1
            continue
        seen.add(key)
        groups[row['user_id']].append((time, row['event']))
    counts, immature, no_entry, equal_time = [0]*len(steps), 0, 0, 0
    for events in groups.values():
        events.sort()
        entries = [t for t,e in events if e == steps[0]]
        if not entries:
            no_entry += 1
            continue
        entry = entries[0]
        if entry + horizon > cutoff:
            immature += 1
            continue
        counts[0] += 1
        previous = entry
        for i, step in enumerate(steps[1:],1):
            if any(t == previous and e == step for t,e in events):
                equal_time += 1
            matches = [t for t,e in events if e == step and previous < t <= entry+horizon]
            if not matches:
                break
            previous = matches[0]
            counts[i] += 1
    return {'steps':[{'event':step,'users':counts[i],
                     'from_entry':counts[i]/counts[0] if counts[0] else None,
                     'from_previous':counts[i]/counts[i-1] if i and counts[i-1] else (1.0 if not i and counts[0] else None),
                     'lost_from_previous':counts[i-1]-counts[i] if i else None} for i,step in enumerate(steps)],
            'excluded_immature_users':immature,'users_without_entry':no_entry,'duplicate_events_removed':duplicate_count,
            'future_events_excluded':future,'ambiguous_same_time_next_steps':equal_time,
            'as_of':as_of,'window_hours':hours,
            'definition':'Closed funnel; earliest entry per user; strictly ordered steps; fully mature entry windows only.'}


def decompose(data):
    groups = {}
    for row in data:
        if not row.get('segment') or row['segment'] in groups:
            raise ValueError('Segments must be named, unique, disjoint and exhaustive')
        values = {key: integer(row.get(key), key, key.startswith('n_')) for key in ['n_before','converted_before','n_after','converted_after']}
        if values['converted_before'] > values['n_before'] or values['converted_after'] > values['n_after']:
            raise ValueError('Conversions cannot exceed denominators')
        groups[row['segment']] = values
    if not groups:
        raise ValueError('At least one segment is required')
    total0, total1 = sum(v['n_before'] for v in groups.values()), sum(v['n_after'] for v in groups.values())
    r0 = sum(v['converted_before'] for v in groups.values())/total0
    r1 = sum(v['converted_after'] for v in groups.values())/total1
    contributions=[]
    for name,v in groups.items():
        w0,w1 = v['n_before']/total0,v['n_after']/total1
        p0,p1 = v['converted_before']/v['n_before'],v['converted_after']/v['n_after']
        mix, within = (w1-w0)*(p0+p1)/2, (p1-p0)*(w0+w1)/2
        contributions.append({'segment':name,'weight_before':w0,'weight_after':w1,'rate_before':p0,'rate_after':p1,
                              'mix_pp':100*mix,'within_pp':100*within,'total_pp':100*(mix+within)})
    total = sum(c['total_pp'] for c in contributions)
    return {'rate_before':r0,'rate_after':r1,'change_pp':100*(r1-r0),'contributions':contributions,
            'mix_pp':sum(c['mix_pp'] for c in contributions),'within_pp':sum(c['within_pp'] for c in contributions),
            'reconciliation_residual_pp':100*(r1-r0)-total,
            'method':'Symmetric Shapley rate decomposition; arithmetic attribution, not causal evidence.'}


def profile(fields, data, keys=None):
    keys = keys or []
    if any(k not in fields for k in keys):
        raise ValueError('Key columns must exist in the CSV')
    duplicates = len(data)-len({tuple(row[k] for k in fields) for row in data})
    key_duplicates = len(data)-len({tuple(row[k] for k in keys) for row in data}) if keys else None
    return {'rows':len(data),'columns':fields,'missing':{k:sum(not row[k].strip() for row in data) for k in fields},
            'duplicate_rows':duplicates,'key_columns':keys,'duplicate_keys':key_duplicates,
            'limitations':['Counts do not establish business validity, freshness, representativeness, or join safety.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command',required=True)
    e = sub.add_parser('experiment')
    for key in ['control-n','control-success','treatment-n','treatment-success']:
        e.add_argument('--'+key,required=True,type=int)
    e.add_argument('--allocation',type=float,default=.5)
    e.add_argument('--alpha',type=float,default=.05)
    e.add_argument('--min-effect',type=float,default=0)
    p = sub.add_parser('power')
    p.add_argument('--baseline',type=float,required=True)
    p.add_argument('--absolute-effect',type=float,required=True)
    p.add_argument('--alpha',type=float,default=.05)
    p.add_argument('--power',dest='target_power',type=float,default=.8)
    f=sub.add_parser('funnel'); f.add_argument('csv'); f.add_argument('--steps',nargs='+',required=True)
    f.add_argument('--as-of',required=True); f.add_argument('--window-hours',type=float,default=168)
    d=sub.add_parser('decompose'); d.add_argument('csv')
    q=sub.add_parser('profile'); q.add_argument('csv'); q.add_argument('--keys',nargs='+')
    args=vars(parser.parse_args()); command=args.pop('command'); source=args.pop('csv',None)
    try:
        if source:
            fields,data=rows(source)
        if command=='experiment': result=experiment(**args)
        elif command=='power': result=power(**args)
        elif command=='funnel': result=funnel(data,**args)
        elif command=='decompose': result=decompose(data)
        else: result=profile(fields,data,**args)
        result['provenance']={'tool':'ChatData 1.0.0','arguments':sys.argv[1:]}
        if source:
            result['provenance']['input_sha256']=hashlib.sha256(Path(source).read_bytes()).hexdigest()
        print(json.dumps(result,indent=2,allow_nan=False))
    except (ValueError, OSError, KeyError, csv.Error) as error:
        print(json.dumps({'error':str(error)}),file=sys.stderr)
        return 2
    return 0

if __name__=='__main__':
    sys.exit(main())
