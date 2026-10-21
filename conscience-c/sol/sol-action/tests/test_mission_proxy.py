import importlib.util
import json
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('mission',Path(__file__).resolve().parents[1]/'app/api/mission.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
J='f67b5768-c949-415d-a938-486897181d92';MID='c74c7fb5-5626-43c5-876d-d26fd47fce0d';R='40a2ed5a-15ec-49d9-838d-2cf8eb752385';C='a'*64
class ProxyTests(unittest.TestCase):
 def body(self,action='verify'):
  data={'job_id':J,'capability':C}
  if action=='verify':data.update(mission_id=MID,request_id=R)
  if action=='receipt':data.update(mission_id=MID,target_request_id=R)
  return {'action':action,'input':data}
 def test_no_registration_or_free_sql(self):
  for action in ['register','create','execute','complete','sql']:
   with self.assertRaises(m.InvalidInput):m.validate({'action':action,'input':{}})
 def test_forbids_client_identity_and_grades(self):
  for key in ['runtime_identity','verdict','result','p_actor','source_csv']:
   b=self.body();b['input'][key]={}
   with self.assertRaises(m.InvalidInput):m.validate(b)
 def test_rejects_noncanonical_references(self):
  for key,value in [('job_id',J.upper()),('request_id',None),('capability','sb_secret_test'),('mission_id','not-a-uuid')]:
   b=self.body();b['input'][key]=value
   with self.assertRaises(m.InvalidInput):m.validate(b)
 def test_identity_added_after_local_loader_and_timestamped(self):
  seen=[];identity={'release_hash':'b'*64,'manifest_hash':'c'*64,'source_commit':'d'*40,'self_hash':'e'*64,'files':{'api/mission.py':'f'*64}}
  def rpc(a,d):seen.append((a,d));return {'ok':True,'job_id':J,'mission_id':MID,'request_id':R,'report':{'technical_verdict':'UNKNOWN'}}
  result=m.dispatch(self.body(),rpc,lambda:identity,lambda:'9'*64)
  self.assertTrue(result['ok']);self.assertEqual(len(seen),1);self.assertEqual(seen[0][1]['runtime_identity']['files'],identity['files']);self.assertTrue(seen[0][1]['runtime_identity']['observed_at'].endswith('Z'))
 def test_early_runtime_failure_never_calls_sql(self):
  seen=[]
  def fail():raise ValueError('no files')
  r=m.dispatch(self.body(),lambda*a:seen.append(a),fail,lambda:'9'*64)
  self.assertEqual(r['status'],'UNKNOWN');self.assertFalse(r['current_reuse_authorized']);self.assertEqual(seen,[])
 def test_status_has_no_runtime_token_injection(self):
  seen=[]
  r=m.dispatch(self.body('status'),lambda a,d:(seen.append(d) or {'ok':True,'job_id':J,'missions':[]}))
  self.assertNotIn('runtime_identity',seen[0]);self.assertEqual(r['missions'],[])
 def test_receipt_reads_once_without_verify(self):
  calls=[]
  r=m.dispatch(self.body('receipt'),lambda a,d:(calls.append((a,d)) or {'ok':True,'job_id':J,'mission_id':MID,'target_request_id':R,'found':False}))
  self.assertEqual(calls[0][0],'receipt');self.assertEqual(len(calls),1);self.assertFalse(r['found'])
 def test_correlated_verify_required(self):
  with self.assertRaises(m.OutcomeUnknown):m.dispatch(self.body(),lambda*a:{'ok':True,'job_id':J,'mission_id':MID,'request_id':'a'},lambda:{},lambda:'9'*64)
 def test_wrong_job_keeps_uncertainty(self):
  with self.assertRaises(m.OutcomeUnknown):m.dispatch(self.body('status'),lambda*a:{'ok':True,'job_id':MID})
 def test_sql_rejection_is_opaque(self):
  r=m.dispatch(self.body('status'),lambda*a:{'ok':False,'error':'private SQL detail'})
  self.assertNotIn('private SQL detail',json.dumps(r));self.assertEqual(r['status'],'REJECTED')
 def test_receipt_identity_mismatch_stays_unknown(self):
  with self.assertRaises(m.OutcomeUnknown):m.dispatch(self.body('receipt'),lambda*a:{'ok':True,'job_id':J,'mission_id':MID,'target_request_id':J})
 def test_response_scrubs_secret_fields_and_strings(self):
  r=m.dispatch(self.body(),lambda*a:{'ok':True,'job_id':J,'mission_id':MID,'request_id':R,'bridge_token':'9'*64,'nested':{'capability':C,'source_csv':'private','note':'9'*64+C}},lambda:{},lambda:'9'*64)
  text=json.dumps(r);self.assertNotIn(C,text);self.assertNotIn('9'*64,text);self.assertNotIn('private',text)
 def test_duplicate_json_rejected(self):
  with self.assertRaises(m.InvalidInput):json.loads('{"action":"status","action":"verify"}',object_pairs_hook=m.unique_object)

if __name__=='__main__':unittest.main(verbosity=2)
