"""Creation recovery crosses a distinct boundary; no retry or fallback."""
import importlib.util
from pathlib import Path
import unittest

APP=Path(__file__).resolve().parents[1]/'app'
spec=importlib.util.spec_from_file_location('guarded_creation_job',APP/'api/job.py')
job=importlib.util.module_from_spec(spec);spec.loader.exec_module(job)
J='31f862f8-c11e-4d5a-bcf6-e410139c0082';R='6603a681-1d77-41dd-80f9-e1b92b3813a2';C='a'*64
RELEASE={k:'b'*64 for k in ['release_hash','manifest_hash','self_hash']};RELEASE['source_commit']='c'*40

class CreationProxyTests(unittest.TestCase):
 def create(self):return {'action':'create','input':{'job_id':J,'capability':C,'request_id':R,'mandate':'Synthetic fixture only','requirements':['Exact cents'],'source_csv':'id,currency,amount\na,EUR,0.10\n','source_origin':{'kind':'declared'}}}
 def reply(self):return {'ok':False,'action':'create','job_id':J,'request_id':R,'status':'REJECTED','sqlstate':'P0001','error':'CSV_ID','durable_refusal':True,'current_reuse_authorized':False}
 def test_creation_injects_only_server_auth_and_calls_once(self):
  calls=[];body=self.create();reply=self.reply()
  result=job.dispatch(body,call_rpc=lambda*a:self.fail('no direct core'),call_bridge=lambda*a:self.fail('no old bridge'),worker=lambda*a:self.fail('no worker'),call_creation=lambda a,d:(calls.append((a,d)) or reply),release_loader=lambda:RELEASE,token_loader=lambda:'d'*64)
  self.assertIs(result,reply);self.assertEqual(calls,[('create_guarded',dict(RELEASE,core_input=body['input'],bridge_token='d'*64))]);self.assertNotIn('bridge_token',result)
 def test_read_exact_creation_receipt_needs_no_server_token(self):
  calls=[];body={'action':'creation_receipt','input':{'job_id':J,'capability':C,'target_request_id':R}}
  reply={'ok':True,'action':'lookup_receipt','job_id':J,'target_request_id':R,'found':False,'current_reuse_authorized':False}
  r=job.dispatch(body,call_creation=lambda a,d:(calls.append((a,d)) or reply),call_bridge=lambda*a:self.fail('old lookup must stay distinct'),release_loader=lambda:self.fail('no release read'),token_loader=lambda:self.fail('no token read'),worker=lambda*a:self.fail('no worker'))
  self.assertIs(r,reply);self.assertEqual(calls,[('lookup_receipt',body['input'])]);self.assertNotIn('effect',r)
 def test_wrong_reference_stays_unknown_without_fallback(self):
  r=self.reply();r['request_id']=J;calls=[]
  with self.assertRaises(job.UncertainOutcome):job.dispatch(self.create(),call_creation=lambda a,d:(calls.append(a) or r),call_rpc=lambda*a:self.fail('no fallback'),release_loader=lambda:RELEASE,token_loader=lambda:'d'*64)
  self.assertEqual(calls,['create_guarded']);self.assertEqual(r['request_id'],J)
 def test_transport_unknown_never_becomes_refusal(self):
  calls=[]
  def send(a,d):calls.append(a);raise job.UncertainOutcome('RPC_OUTCOME_UNKNOWN')
  with self.assertRaises(job.UncertainOutcome):job.dispatch(self.create(),call_creation=send,release_loader=lambda:RELEASE,token_loader=lambda:'d'*64,call_bridge=lambda*a:self.fail('no retry'))
  self.assertEqual(calls,['create_guarded'])
 def test_missing_server_auth_sends_nothing(self):
  calls=[]
  def unavailable():raise ValueError('unavailable')
  with self.assertRaises(job.UncertainOutcome):job.dispatch(self.create(),call_creation=lambda*a:calls.append(a),release_loader=lambda:RELEASE,token_loader=unavailable)
  self.assertEqual(calls,[])
 def test_client_cannot_supply_guard_authority(self):
  body=self.create();body['input']['bridge_token']='e'*64
  with self.assertRaises(job.InputError):job.validate_request(body)
 def test_creation_receipt_requires_original_uuid(self):
  for data in [{'job_id':J,'capability':C},{'job_id':J,'capability':C,'target_request_id':'not-uuid'},{'job_id':J,'capability':C,'target_request_id':R,'request_id':J}]:
   with self.assertRaises(job.InputError):job.validate_request({'action':'creation_receipt','input':data})
 def test_legacy_receipt_stays_on_original_bridge(self):
  calls=[];body={'action':'receipt','input':{'job_id':J,'capability':C,'target_request_id':R}};reply={'ok':True,'action':'lookup_receipt','job_id':J,'target_request_id':R,'found':False}
  self.assertIs(job.dispatch(body,call_bridge=lambda a,d:(calls.append(a) or reply),call_creation=lambda*a:self.fail('not a creation lookup')),reply);self.assertEqual(calls,['lookup_receipt'])

if __name__=='__main__':unittest.main(verbosity=2)
