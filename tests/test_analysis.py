import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'plugins/chatdata'
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
A=load('analyze',P/'scripts/analyze.py')
I=load('installer',ROOT/'scripts/install.py')

class ExperimentTests(unittest.TestCase):
    def test_known_wilson_interval(self):
        low,high=A.wilson(50,100)
        self.assertAlmostEqual(low,0.4038315304,places=9)
        self.assertAlmostEqual(high,0.5961684696,places=9)
    def test_known_effect(self):
        r=A.experiment(1000,100,1000,140,min_effect=.01)
        self.assertAlmostEqual(r['percentage_point_difference'],4)
        self.assertAlmostEqual(r['relative_lift'],.4)
        self.assertGreater(r['difference_interval'][0],.01)
        self.assertEqual(r['srm_p_value'],1)
        self.assertIn('pending_design',r['result'])
    def test_assignment_mismatch_blocks_apparent_winner(self):
        self.assertEqual(A.experiment(1000,100,1500,300)['result'],'blocked_srm')
    def test_planned_unequal_allocation_is_not_srm(self):
        self.assertEqual(A.experiment(1000,100,3000,330,allocation=.75)['srm_p_value'],1)
    def test_zero_baseline_has_no_relative_lift(self):
        r=A.experiment(100,0,100,5)
        self.assertIsNone(r['relative_lift']); self.assertIsNone(r['two_sided_p_value'])
        self.assertEqual(r['result'],'sparse_data_review_required')
    def test_all_successes_and_no_successes_have_nonzero_uncertainty(self):
        for x in [0,100]:
            low,high=A.experiment(100,x,100,x)['difference_interval']
            self.assertLess(low,0); self.assertGreater(high,0)
    def test_tiny_assignments_not_validated(self):
        self.assertEqual(A.experiment(2,1,2,1)['result'],'insufficient_assignment_counts')
    def test_no_difference_is_inconclusive(self):
        self.assertEqual(A.experiment(1000,100,1000,100)['result'],'inconclusive_for_minimum_effect')
    def test_practical_effect_differs_from_statistical(self):
        r=A.experiment(1000,100,1000,140,min_effect=.05)
        self.assertEqual(r['result'],'inconclusive_for_minimum_effect')
    def test_invalid_counts_rejected(self):
        for args in [(0,0,10,1),(10,11,10,1),(-1,0,10,1),(True,0,10,1),(10.5,1,10,1)]:
            with self.assertRaises(ValueError): A.experiment(*args)
    def test_nonfinite_inputs_rejected(self):
        for key in ['allocation','alpha','min_effect']:
            with self.assertRaises(ValueError): A.experiment(100,10,100,10,**{key:float('nan')})
    def test_swap_arms_reverses_interval(self):
        a=A.experiment(1000,100,1000,140); b=A.experiment(1000,140,1000,100)
        self.assertAlmostEqual(a['difference_interval'][0],-b['difference_interval'][1])
    def test_power_reference_and_monotonicity(self):
        self.assertEqual(A.power(.1,.02)['per_arm'],3841)
        self.assertGreater(A.power(.1,.01)['per_arm'],A.power(.1,.02)['per_arm'])
        self.assertGreater(A.power(.1,.02,target_power=.9)['per_arm'],3841)
    def test_power_rejects_impossible_design(self):
        for effect in [0,.9,float('nan')]:
            with self.assertRaises(ValueError): A.power(.1,effect)

class FunnelTests(unittest.TestCase):
    def setUp(self): self.data=A.rows(P/'examples/funnel.csv')[1]
    def run_funnel(self,data=None,**kwargs):
        return A.funnel(data if data is not None else self.data,['visit','signup','purchase'],kwargs.pop('as_of','2026-01-05T00:00:00Z'),**kwargs)
    def test_order_maturity_duplicates_and_horizon(self):
        r=self.run_funnel(window_hours=48)
        self.assertEqual([s['users'] for s in r['steps']],[3,2,1])
        self.assertEqual(r['excluded_immature_users'],1); self.assertEqual(r['duplicate_events_removed'],1)
    def test_reversed_input_is_identical(self):
        self.assertEqual(self.run_funnel(window_hours=48),self.run_funnel(list(reversed(self.data)),window_hours=48))
    def test_tied_timestamps_not_order(self):
        data=[{'user_id':'x','event':e,'timestamp':'2026-01-01T00:00:00Z'} for e in ['visit','signup','purchase']]
        r=self.run_funnel(data,window_hours=48)
        self.assertEqual([s['users'] for s in r['steps']],[1,0,0]); self.assertEqual(r['ambiguous_same_time_next_steps'],1)
    def test_empty_denominator_null(self):
        self.assertIsNone(self.run_funnel([],window_hours=48)['steps'][0]['from_entry'])
    def test_future_events_excluded(self):
        r=self.run_funnel(window_hours=1,as_of='2026-01-01T00:30:00Z')
        self.assertGreater(r['future_events_excluded'],0)
    def test_timezone_required(self):
        with self.assertRaises(ValueError): self.run_funnel(as_of='2026-01-05')
    def test_invalid_event_not_silently_dropped(self):
        with self.assertRaises(ValueError): self.run_funnel([{'user_id':'','event':'visit','timestamp':'2026-01-01T00:00:00Z'}])
    def test_invalid_horizon_rejected(self):
        for value in [0,-1,float('inf')]:
            with self.assertRaises(ValueError): self.run_funnel(window_hours=value)
    def test_maturity_boundary_included(self):
        r=self.run_funnel(window_hours=48,as_of='2026-01-03T00:00:00Z')
        self.assertEqual(r['steps'][0]['users'],3)

class DecompositionTests(unittest.TestCase):
    def setUp(self): self.data=A.rows(P/'examples/mix-shift.csv')[1]
    def test_mix_only_drop(self):
        r=A.decompose(self.data)
        self.assertAlmostEqual(r['rate_before'],.17); self.assertAlmostEqual(r['rate_after'],.08)
        self.assertAlmostEqual(r['mix_pp'],-9); self.assertAlmostEqual(r['within_pp'],0)
        self.assertAlmostEqual(r['reconciliation_residual_pp'],0)
    def test_within_only_drop(self):
        r=A.decompose([dict(segment='all',n_before='100',converted_before='20',n_after='100',converted_after='10')])
        self.assertAlmostEqual(r['mix_pp'],0); self.assertAlmostEqual(r['within_pp'],-10)
    def test_interaction_reconciles(self):
        self.data[0]['converted_after']='20'
        r=A.decompose(self.data)
        self.assertAlmostEqual(r['mix_pp']+r['within_pp'],r['change_pp'])
    def test_undefined_rate_refused(self):
        self.data[0]['n_after']='0'; self.data[0]['converted_after']='0'
        with self.assertRaises(ValueError): A.decompose(self.data)
    def test_duplicate_segment_refused(self):
        with self.assertRaises(ValueError): A.decompose(self.data+self.data)

class PackagingTests(unittest.TestCase):
    def test_csv_profile_counts(self):
        fields,data=A.rows(P/'examples/funnel.csv'); r=A.profile(fields,data,fields)
        self.assertEqual(r['duplicate_rows'],1); self.assertEqual(r['duplicate_keys'],1)
    def test_invalid_csv_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'bad.csv'; path.write_text('a,a\n1,2\n')
            with self.assertRaises(ValueError): A.rows(path)
    def test_cli_provenance(self):
        r=subprocess.run([sys.executable,str(P/'scripts/analyze.py'),'decompose',str(P/'examples/mix-shift.csv')],capture_output=True,text=True,check=True)
        self.assertEqual(len(json.loads(r.stdout)['provenance']['input_sha256']),64)
        self.assertEqual(json.loads(r.stdout)['provenance']['tool'], 'ChatData '+json.loads((P/'scripts/package-info.json').read_text())['version'])
    def test_cli_bad_input_fails(self):
        r=subprocess.run([sys.executable,str(P/'scripts/analyze.py'),'experiment','--control-n','0','--control-success','0','--treatment-n','5','--treatment-success','1'],capture_output=True,text=True)
        self.assertEqual(r.returncode,2); self.assertIn('error',json.loads(r.stderr))
    def test_project_installs_and_refuses_overwrite(self):
        for client,folder in [('cursor','.cursor'),('codex','.agents')]:
            with self.subTest(client=client), tempfile.TemporaryDirectory(prefix='space in path ') as tmp:
                existing=Path(tmp)/folder/'skills/unrelated'; existing.mkdir(parents=True); (existing/'keep').write_text('preserve')
                r=I.install(client,tmp); self.assertEqual(r['skills'],16)
                target=Path(tmp)/folder/'skills/chatdata-experiment-analysis'
                self.assertTrue((target/'scripts/analyze.py').is_file())
                text=(target/'SKILL.md').read_text(); self.assertIn('name: chatdata-experiment-analysis',text)
                self.assertNotIn('../../references/',text)
                with self.assertRaises(ValueError): I.install(client,tmp)
                self.assertEqual((existing/'keep').read_text(),'preserve')
    def test_hook_has_branding_and_no_settings_mutation(self):
        r=subprocess.run(['node',str(P/'scripts/session-start.js')],text=True,capture_output=True,check=True)
        context=json.loads(r.stdout)['hookSpecificOutput']['additionalContext']
        self.assertIn('ChatData '+json.loads((P/'scripts/package-info.json').read_text())['version'],context)
        self.assertIn('Dashboard linking is required for ChatData analysis',context)
        self.assertNotIn('skills still work locally if reporting is disconnected',context)

    def test_readme_uses_dashboard_linking_without_legacy_prompt_commands(self):
        readme=(ROOT/'README.md').read_text()
        self.assertIn('dashboard creates the complete command',readme)
        self.assertNotIn('telemetry.py connect --client',readme)

if __name__=='__main__': unittest.main()
