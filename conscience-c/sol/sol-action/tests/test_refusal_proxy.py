"""The proxy delegates existing-job commands to durable recovery, never retries them."""
import importlib.util
from pathlib import Path
import unittest

APP=Path(__file__).resolve().parents[1]/'app'
spec=importlib.util.spec_from_file_location('refusal_job',APP/'api/job.py')
job=importlib.util.module_from_spec(spec);spec.loader.exec_module(job)
J='31f862f8-c11e-4d5a-bcf6-e410139c0082'
R='6603a681-1d77-41dd-80f9-e1b92b3813a2'
C='a'*64

class RefusalProxyTests(unittest.TestCase):
 def body(self,action):
  data={'job_id':J,'capability':C,'request_id':R}
  if action in {'complete','verify'}:data['expected_step_id']=action
  if action=='reconcile':data['target_request_id']='a948e700-ab3e-4336-9f82-a91cb8293486'
  if action=='create':data.update(mandate='Synthetic fixture',requirements=['Exact cents'],source_csv='id,currency,amount\na,EUR,0.10\n',source_origin={'kind':'declared'})
  return {'action':action,'input':data}
 def test_existing_commands_cross_boundary_once(self):
  for action in ['verify','complete','reconcile']:
   calls=[]
   def bridge(a,d):
    calls.append((a,d));return {'ok':False,'status':'REJECTED','action':action,'job_id':J,'request_id':R,'sqlstate':'P0001','error':'FRESH_VERIFICATION_REQUIRED','durable_refusal':True,'terminal':True,'effect':'NONE_SQL_TRANSACTION_ROLLED_BACK'}
   result=job.dispatch(self.body(action),call_rpc=lambda*a:self.fail('direct core must not be called'),call_bridge=bridge,worker=lambda*a:self.fail('worker must not run'))
   self.assertEqual(calls,[('execute',{'core_action':action,'core_input':self.body(action)['input']})])
   self.assertTrue(result['durable_refusal']);self.assertEqual(result['effect'],'NONE_SQL_TRANSACTION_ROLLED_BACK')
 def test_unknown_transport_is_never_reclassified(self):
  calls=[]
  def bridge(a,d):calls.append(a);raise job.UncertainOutcome('RPC_OUTCOME_UNKNOWN')
  with self.assertRaises(job.UncertainOutcome):job.dispatch(self.body('complete'),call_bridge=bridge,call_rpc=lambda*a:self.fail('no core fallback'))
  self.assertEqual(calls,['execute'])
 def test_generic_denial_does_not_claim_no_effect(self):
  result=job.dispatch(self.body('complete'),call_bridge=lambda*a:{'ok':False,'status':'REJECTED','error':'NOT_AUTHORIZED_OR_INVALID_REFERENCE'})
  self.assertNotIn('effect',result);self.assertNotIn('terminal',result)
 def test_historical_refusal_never_acquires_current_authority(self):
  historical={'ok':False,'action':'complete','status':'HISTORICAL_NOT_CURRENT','historical_status':'REJECTED','job_id':J,'request_id':R,'durable_refusal':True,'current_reuse_authorized':False,'deduplicated':True}
  result=job.dispatch(self.body('complete'),call_bridge=lambda*a:historical)
  self.assertEqual(result,historical);self.assertFalse(result['current_reuse_authorized'])
 def test_receipt_reads_do_not_execute_any_command(self):
  calls=[];body={'action':'receipt','input':{'job_id':J,'capability':C,'target_request_id':R}}
  response=job.dispatch(body,call_bridge=lambda a,d:(calls.append((a,d)) or {'ok':True,'action':'lookup_receipt','job_id':J,'target_request_id':R,'found':False}),call_rpc=lambda*a:self.fail('no core'),worker=lambda*a:self.fail('no worker'))
  self.assertEqual(calls,[('lookup_receipt',body['input'])]);self.assertFalse(response['found'])

if __name__=='__main__':unittest.main(verbosity=2)
