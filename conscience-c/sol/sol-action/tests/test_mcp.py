import importlib.util
import json
import hashlib
import tempfile
import unittest
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('public_mcp',BASE/'app/api/mcp.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class PublicSurfaceTests(unittest.TestCase):
    def test_initialize_pinned_protocol(self):
        r=m.dispatch({'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-06-18'}})
        self.assertEqual(r['result']['protocolVersion'],'2025-06-18')
        self.assertEqual(r['result']['capabilities'],{'tools':{}})

    def test_only_readonly_tool_has_empty_arguments(self):
        tools=m.dispatch({'jsonrpc':'2.0','id':1,'method':'tools/list'})['result']['tools']
        self.assertEqual([t['name'] for t in tools],['release_manifest'])
        self.assertFalse(tools[0]['inputSchema']['additionalProperties'])
        self.assertTrue(tools[0]['annotations']['readOnlyHint'])
        self.assertFalse(tools[0]['annotations']['destructiveHint'])

    def test_arbitrary_job_argument_does_not_call_loader(self):
        def forbidden(): raise AssertionError('loader must not run')
        r=m.dispatch({'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':'release_manifest','arguments':{'job_id':'private'}}},forbidden)
        self.assertTrue(r['result']['isError'])

    def test_determinism_and_limits_are_in_returned_data(self):
        value={'available':True,'release_hash':'a'*64,'source_commit':'b'*40,'source_files':{},'does_not_establish':['correctness']}
        req={'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':'release_manifest','arguments':{}}}
        self.assertEqual(m.dispatch(req,lambda:value),m.dispatch(req,lambda:value))
        self.assertEqual(json.loads(m.dispatch(req,lambda:value)['result']['content'][0]['text'])['does_not_establish'],['correctness'])

    def test_internal_failure_never_becomes_available(self):
        def broken(): raise RuntimeError('secret value should not be echoed')
        r=m.dispatch({'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':'release_manifest'}},broken)
        self.assertTrue(r['result']['isError'])
        self.assertNotIn('secret value',json.dumps(r))

    def test_notifications_do_not_produce_rpc_response(self):
        self.assertIsNone(m.dispatch({'jsonrpc':'2.0','method':'notifications/initialized'}))

    def test_non_object_and_unsafe_id_are_rejected(self):
        self.assertEqual(m.dispatch([])['error']['code'],-32600)
        self.assertEqual(m.dispatch({'jsonrpc':'2.0','id':9007199254740992,'method':'ping'})['error']['code'],-32600)

    def test_manifest_reads_exact_deployed_bytes_and_refuses_change(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'api').mkdir();(p/'api/mcp.py').write_bytes(b'mcp');(p/'api/job.py').write_bytes(b'job');(p/'api/mission.py').write_bytes(b'mission');(p/'bridge_runtime.py').write_bytes(b'bridge')
            files={name:hashlib.sha256((p/name).read_bytes()).hexdigest() for name in ['api/mcp.py','api/job.py','api/mission.py','bridge_runtime.py']}
            (p/'release-source.json').write_text(json.dumps({'schema':'SOL_ACTION_RELEASE_SOURCE/v1','files':files}))
            (p/'build-info.json').write_text(json.dumps({'source_commit':'b'*40}))
            self.assertTrue(m.release_manifest(p)['available'])
            (p/'api/mission.py').write_bytes(b'changed')
            with self.assertRaises(ValueError):m.release_manifest(p)

if __name__=='__main__':unittest.main()
