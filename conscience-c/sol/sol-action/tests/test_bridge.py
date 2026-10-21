import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("sol_action_integration_job", ROOT / "app/api/job.py")
job = importlib.util.module_from_spec(spec)
spec.loader.exec_module(job)
bridge = job.bridge_runtime
CSV = 'id,currency,amount\na,EUR,0.1\nb,EUR,0.2\n'
J = '10000000-0000-4000-8000-000000000001'
P = '10000000-0000-4000-8000-000000000002'
R = '10000000-0000-4000-8000-000000000003'
CAP = 'a' * 64
TOKEN = 'b' * 64  # synthetic fixture only, not a deployed credential
RELEASE = {'manifest_hash': 'c' * 64, 'source_commit': 'd' * 40, 'release_hash': 'e' * 64, 'self_hash': 'f' * 64}


def produce():
    return {'action': 'produce', 'input': {'job_id': J, 'capability': CAP, 'request_id': P, 'result_request_id': R, 'expected_step_id': 'produce'}}


def binding():
    return {'ok': True, 'status': 'BOUND_RELEASE', 'job_id': J, 'production_request_id': P,
            'release_hash': RELEASE['release_hash'], 'self_hash': RELEASE['self_hash'],
            'binding_granted': True, 'binding_and_begin_atomic': True,
            'begin_receipt': {'ok': True, 'status': 'RECORDED', 'begin_granted': True,
                              'job_id': J, 'production_request_id': P,
                              'source_csv': CSV, 'source_sha256': hashlib.sha256(CSV.encode()).hexdigest()}}


class DispatchTests(unittest.TestCase):
    def dispatch(self, body, **kwargs):
        return job.dispatch(body, release_loader=lambda: dict(RELEASE), token_loader=lambda: TOKEN, **kwargs)

    def test_receipt_is_read_only_and_forwards_exact_original_uuid(self):
        calls = []
        data = {'job_id': J, 'capability': CAP, 'target_request_id': P}
        expected = {'ok': True, 'status': 'HISTORICAL_NOT_CURRENT', 'job_id': J, 'target_request_id': P, 'found': True, 'receipt': {'action': 'reconcile', 'request_id': P}}
        result = self.dispatch({'action': 'receipt', 'input': data}, call_bridge=lambda action, value: calls.append((action, value)) or expected, call_rpc=lambda *_: self.fail('old RPC called'), worker=lambda _: self.fail('worker called'))
        self.assertEqual(expected, result)
        self.assertEqual([('lookup_receipt', data)], calls)
        self.assertNotIn('request_id', calls[0][1])

    def test_receipt_absent_stays_unknown(self):
        unknown = {'ok': True, 'status': 'UNKNOWN', 'found': False, 'receipt': None, 'current_reuse_authorized': False}
        result = self.dispatch({'action': 'receipt', 'input': {'job_id': J, 'capability': CAP, 'target_request_id': P}}, call_bridge=lambda *_: unknown)
        self.assertIsNone(result['receipt'])
        self.assertFalse(result['found'])
        self.assertFalse(result['current_reuse_authorized'])

    def test_receipt_unknown_fields_or_new_uuid_are_rejected(self):
        for field, value in [('request_id', R), ('bridge_token', TOKEN), ('verdict', 'PASS')]:
            with self.subTest(field=field):
                with self.assertRaises(job.InputError):
                    self.dispatch({'action': 'receipt', 'input': {'job_id': J, 'capability': CAP, 'target_request_id': P, field: value}}, call_bridge=lambda *_: self.fail('invalid body reached network'))

    def test_atomic_binding_receipt_runs_worker_and_result_once_without_second_begin(self):
        calls = []
        def old_rpc(action, data):
            calls.append(action)
            self.assertEqual('result', action)
            self.assertEqual(P, data['production_request_id'])
            self.assertEqual(R, data['request_id'])
            self.assertNotIn('bridge_token', data)
            return {'ok': True, 'action': 'result', 'result': data['result']}
        def bridge_rpc(action, data):
            calls.append(action)
            self.assertEqual('bind', action)
            self.assertEqual(P, data['production_request_id'])
            self.assertEqual(TOKEN, data['bridge_token'])
            return binding()
        response = self.dispatch(produce(), call_bridge=bridge_rpc, call_rpc=old_rpc)
        self.assertEqual(['bind', 'result'], calls)
        self.assertEqual('0.30', response['result']['totals'][0]['amount'])
        self.assertNotIn(TOKEN, json.dumps(response))

    def test_historical_binding_never_grants_worker_or_begin(self):
        for changes in [{'binding_granted': False}, {'status': 'HISTORICAL_NOT_CURRENT'}, {'deduplicated': True}]:
            with self.subTest(changes=changes):
                receipt = binding(); receipt.update(changes)
                result = self.dispatch(produce(), call_bridge=lambda *_: receipt, call_rpc=lambda *_: self.fail('duplicate reached core'), worker=lambda _: self.fail('duplicate worker'))
                self.assertEqual('OUTCOME_UNKNOWN', result['status'])
                self.assertTrue(result['pending'])

    def test_binding_requires_exact_correlation_and_atomic_flag(self):
        for field, value in [('job_id', R), ('production_request_id', R), ('release_hash', '1' * 64), ('self_hash', '2' * 64), ('binding_and_begin_atomic', False), ('begin_receipt', None)]:
            with self.subTest(field=field):
                receipt = binding(); receipt[field] = value
                result = self.dispatch(produce(), call_bridge=lambda *_: receipt, call_rpc=lambda *_: self.fail('wrong binding reached core'), worker=lambda _: self.fail('wrong binding worker'))
                self.assertEqual('OUTCOME_UNKNOWN', result['status'])
                self.assertTrue(result['pending'])

    def test_lost_atomic_bind_does_not_retry(self):
        calls = []
        def lost(*args):
            calls.append(args[0]); raise job.UncertainOutcome('lost')
        with self.assertRaises(job.UncertainOutcome):
            self.dispatch(produce(), call_bridge=lost, call_rpc=lambda *_: self.fail('second begin'), worker=lambda _: self.fail('unknown bind worker'))
        self.assertEqual(['bind'], calls)

    def test_wrong_inner_begin_production_uuid_cannot_run_worker(self):
        receipt = binding(); receipt['begin_receipt']['production_request_id'] = R
        with self.assertRaises(job.UncertainOutcome):
            self.dispatch(produce(), call_bridge=lambda *_: receipt, call_rpc=lambda *_: self.fail('wrong inner begin'), worker=lambda _: self.fail('wrong inner begin worker'))

    def test_inner_begin_rejection_does_not_erase_atomic_reservation(self):
        receipt = binding(); receipt['begin_receipt'] = {'ok': False, 'status': 'REJECTED', 'sqlstate': 'P0001', 'effect': 'NONE_SQL_TRANSACTION_ROLLED_BACK'}
        result = self.dispatch(produce(), call_bridge=lambda *_: receipt, call_rpc=lambda *_: self.fail('core called'))
        self.assertEqual('OUTCOME_UNKNOWN', result['status'])
        self.assertTrue(result['pending'])
        self.assertNotIn('effect', result)

    def test_result_rejection_keeps_atomic_begin_pending(self):
        result = self.dispatch(produce(), call_bridge=lambda *_: binding(), call_rpc=lambda *_: {'ok': False, 'status': 'REJECTED', 'effect': 'NONE_SQL_TRANSACTION_ROLLED_BACK'})
        self.assertTrue(result['pending'])
        self.assertEqual('OUTCOME_UNKNOWN', result['status'])
        self.assertNotIn('effect', result)

    def test_client_cannot_supply_bridge_secret(self):
        body = produce(); body['input']['bridge_token'] = TOKEN
        with self.assertRaises(job.InputError):
            self.dispatch(body, call_bridge=lambda *_: self.fail('client secret accepted'))

    def test_old_csv_worker_code_is_identical_and_frozen_corpus_still_matches(self):
        old = ROOT.parents[1] / 'outputs/sol-action/app/api/job.py'
        def segment(path):
            source = path.read_text(); tree = ast.parse(source)
            return ast.get_source_segment(source, next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'compute_csv'))
        self.assertEqual(segment(old), segment(ROOT / 'app/api/job.py'))
        corpus = json.loads((ROOT.parents[1] / 'outputs/sol-action/audit/independent-corpus.json').read_text())
        for case in corpus['csv_cases']:
            with self.subTest(case=case['id']):
                try: actual = job.compute_csv(case['csv'])
                except job.InputError: self.assertFalse(case['expected']['accepted'])
                else: self.assertEqual(case['expected']['result'], actual)


class ReleaseTests(unittest.TestCase):
    def fixture(self, root):
        (root / 'api').mkdir()
        (root / 'api/job.py').write_bytes(b'worker fixture\n')
        (root / 'bridge_runtime.py').write_bytes(b'helper fixture\n')
        files = {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in ['api/job.py', 'bridge_runtime.py']}
        manifest = {'schema': 'SOL_ACTION_RELEASE_SOURCE/v1', 'files': files}
        (root / 'release-source.json').write_text(json.dumps(manifest, sort_keys=True) + '\n')
        (root / 'build-info.json').write_text(json.dumps({'schema': 'SOL_ACTION_BUILD_INFO/v1', 'source_commit': 'c' * 40}) + '\n')
        return manifest

    def test_reads_actual_files_and_hashes_exact_manifest_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); manifest = self.fixture(root); result = bridge.load_release(root)
            actual_manifest_hash = hashlib.sha256((root / 'release-source.json').read_bytes()).hexdigest()
            self.assertEqual(actual_manifest_hash, result['manifest_hash'])
            self.assertEqual(manifest['files']['api/job.py'], result['self_hash'])
            self.assertEqual(hashlib.sha256((actual_manifest_hash + ':' + 'c' * 40).encode()).hexdigest(), result['release_hash'])

    def test_worker_file_changed_is_refused_before_network(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); self.fixture(root); (root / 'api/job.py').write_bytes(b'changed\n')
            with self.assertRaises(bridge.ReleaseCheckError): bridge.load_release(root)

    def test_helper_file_changed_is_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); self.fixture(root); (root / 'bridge_runtime.py').write_bytes(b'changed\n')
            with self.assertRaises(bridge.ReleaseCheckError): bridge.load_release(root)

    def test_path_outside_root_is_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); manifest = self.fixture(root); manifest['files']['../outside'] = 'a' * 64
            (root / 'release-source.json').write_text(json.dumps(manifest))
            with self.assertRaises(bridge.ReleaseCheckError): bridge.load_release(root)

    def test_manifest_must_not_contain_itself_or_build_info(self):
        for name in ['release-source.json', 'build-info.json']:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary); manifest = self.fixture(root); manifest['files'][name] = 'a' * 64
                (root / 'release-source.json').write_text(json.dumps(manifest))
                with self.assertRaises(bridge.ReleaseCheckError): bridge.load_release(root)

    def test_duplicate_json_keys_are_not_silently_reinterpreted(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); self.fixture(root); (root / 'build-info.json').write_text('{"schema":"SOL_ACTION_BUILD_INFO/v1","source_commit":"' + 'c' * 40 + '","source_commit":"' + 'd' * 40 + '"}')
            with self.assertRaises(bridge.ReleaseCheckError): bridge.load_release(root)

    def test_runtime_token_is_only_loaded_from_private_environment(self):
        with mock.patch.dict(os.environ, {'SOL_BRIDGE_TOKEN': TOKEN}): self.assertEqual(TOKEN, bridge.server_token())
        with mock.patch.dict(os.environ, {'SOL_BRIDGE_TOKEN': ''}):
            with self.assertRaises(bridge.ReleaseCheckError): bridge.server_token()


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromModule(__import__(__name__))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    receipt = {'schema': 'SOL_ACTION_BRIDGE_LOCAL_TEST/v1', 'observed_at': datetime.now(timezone.utc).isoformat(), 'test_methods': result.testsRun, 'csv_cases': 40, 'failures': len(result.failures), 'errors': len(result.errors), 'successful': result.wasSuccessful(), 'remote_mutations': False, 'sql_execution': 'NOT_EXECUTED_LOCALLY_NO_POSTGRES', 'source_sha256': {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in [ROOT/'backend.sql', ROOT/'app/api/job.py', ROOT/'app/bridge_runtime.py']}}
    (ROOT / 'evidence/bridge-local-tests.json').write_text(json.dumps(receipt, indent=2) + '\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
