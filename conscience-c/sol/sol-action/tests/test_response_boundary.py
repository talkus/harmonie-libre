"""Reference/JSON ambiguity must never become evidence or a repeated action."""
import importlib.util,io,json,os,types,unittest
from pathlib import Path
APP=Path(os.environ.get('SOL_TEST_APP',Path(__file__).resolve().parents[1]/'app'))
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
job=load('boundary_job',APP/'api/job.py');mcp=load('boundary_mcp',APP/'api/mcp.py')
J='31f862f8-c11e-4d5a-bcf6-e410139c0082';R='6603a681-1d77-41dd-80f9-e1b92b3813a2';OTHER='a948e700-ab3e-4336-9f82-a91cb8293486'

class BoundaryTests(unittest.TestCase):
 def body(self):return {'action':'complete','input':{'job_id':J,'capability':'a'*64,'request_id':R,'expected_step_id':'complete'}}
 def reject(self):return {'ok':False,'status':'REJECTED','action':'complete','job_id':J,'request_id':R,'sqlstate':'P0001','error':'FRESH_VERIFICATION_REQUIRED'}
 def test_identity_is_never_repaired(self):
  for key,value in [('job_id',OTHER),('request_id',OTHER),('action','verify')]:
   calls=[];r=self.reject();r[key]=value
   with self.assertRaises(job.UncertainOutcome):job.dispatch(self.body(),call_bridge=lambda a,d:(calls.append(a) or r))
   self.assertEqual(calls,['execute']);self.assertEqual(r[key],value)
 def test_sqlstate_alone_never_proves_absence_of_effect(self):
  original=self.reject();r=job.dispatch(self.body(),call_bridge=lambda*a:original)
  self.assertIs(r,original);self.assertNotIn('effect',r);self.assertNotIn('durable_refusal',r)
 def test_real_receipt_fields_are_preserved_without_new_claims(self):
  r=dict(self.reject(),effect='NONE_SQL_TRANSACTION_ROLLED_BACK',effect_scope='CONTROLLED_CORE_DISPATCH_SUBTRANSACTION_ONLY',durable_refusal=True)
  self.assertEqual(job.dispatch(self.body(),call_bridge=lambda*a:r),r)
 def test_non_object_and_missing_original_reference_stay_unknown(self):
  for value in [None,[],True,{'ok':True},{'ok':False,'sqlstate':'P0001'}]:
   with self.assertRaises(job.UncertainOutcome):job.dispatch(self.body(),call_bridge=lambda*a:value)
 def test_wrong_receipt_target_does_not_trigger_command(self):
  b={'action':'receipt','input':{'job_id':J,'capability':'a'*64,'target_request_id':R}};calls=[]
  with self.assertRaises(job.UncertainOutcome):job.dispatch(b,call_bridge=lambda a,d:(calls.append(a) or {'ok':True,'action':'lookup_receipt','job_id':J,'target_request_id':OTHER,'found':True}))
  self.assertEqual(calls,['lookup_receipt'])
 def test_job_and_mcp_duplicate_json_never_dispatch(self):
  for module,raw in [(job,b'{"action":"status","action":"complete"}'),(mcp,b'{"jsonrpc":"2.0","id":1,"method":"ping","method":"tools/call"}')]:
   calls=[];answers=[];old=module.dispatch;module.dispatch=lambda *a:calls.append(a)
   fake=types.SimpleNamespace(path='/',headers={'Content-Type':'application/json','Content-Length':str(len(raw))},rfile=io.BytesIO(raw),reply=lambda *a:answers.append(a),allowed_origin=lambda:True,allowed_protocol=lambda:True)
   try:module.handler.do_POST(fake)
   finally:module.dispatch=old
   self.assertEqual(calls,[]);self.assertEqual(answers[0][0],400)
 def test_nested_duplicate_json_is_rejected(self):
  for module in [job,mcp]:
   with self.assertRaises(ValueError):json.loads('{"input":{"request_id":"a","request_id":"b"}}',object_pairs_hook=module.unique_object)

if __name__=='__main__':unittest.main(verbosity=2)
