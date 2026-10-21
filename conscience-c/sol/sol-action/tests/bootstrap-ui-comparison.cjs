'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const fixturePath=path.join(__dirname,'fixtures/recovery-world-v033.cjs'),fixtureBody=fs.readFileSync(fixturePath,'utf8'),m={exports:{}};
new Function('require','module','__dirname',fixtureBody+'\nmodule.exports.World=World;')(require,m,path.dirname(fixturePath));
const KEY='sol-action-session-v1',CSV='id,currency,amount\none,EUR,0.10\n',HASH='a'.repeat(64),clone=x=>JSON.parse(JSON.stringify(x));
function historical(r){return {...clone(r),status:'HISTORICAL_NOT_CURRENT',historical_status:r.status,needs_current_revalidation:true,current_reuse_authorized:false,automatic_retry:false,worker_reexecuted:false};}
class World extends m.exports.World{
 constructor(source,mode){super(source,mode);this.store.delete(KEY);this.jobExists=false;this.negative=null;this.readLost=false;this.expectedCap=null;}
 async fetch(url,init){
  if(url==='/provider-observation.json')return this.response(null);
  assert.equal(url,'/api/job');const {action,input}=JSON.parse(init.body);this.calls.push({action,job_id:input.job_id,request_id:input.request_id||null,target_request_id:input.target_request_id||null});
  const common={action,job_id:input.job_id,request_id:input.request_id,automatic_retry:false,current_reuse_authorized:false};
  if(action==='create'){
   this.original=input.request_id;this.expectedCap=input.capability;
   if(this.mode==='ambiguous')throw Error('synthetic unresolved transport');
   if(this.mode==='success-lost'){this.jobExists=true;this.outcomes.set(input.request_id,{...common,ok:true,status:'RECORDED',pending:false,next_step_id:'produce',source_sha256:HASH});throw Error('synthetic positive response discarded');}
   this.negative={...common,ok:false,status:'REJECTED',error:'DAILY_JOB_LIMIT',sqlstate:'P0001',effect:'NONE_SQL_TRANSACTION_ROLLED_BACK',effect_scope:'CONTROLLED_CORE_DISPATCH_SUBTRANSACTION_ONLY',core_effect_scope:'THIS_RPC_SQL_TRANSACTION_ONLY',receipt_recording_effect:'APPEND_ONLY_CREATION_GUARD_RECEIPT_RECORDED',business_effect:'NONE_CORE_ACTION_ROLLED_BACK',receipt_kind:'CONTROLLED_CREATION_REFUSAL',terminal:true,durable_refusal:true,worker_reexecuted:false};
   if(this.mode==='delivered')return this.response(this.negative);
   throw Error('synthetic negative response discarded');
  }
  if(action==='creation_receipt'){
   if(this.mode==='lookup-lost'&&!this.readLost){this.readLost=true;throw Error('synthetic read response discarded');}
   if(input.capability!==this.expectedCap)return this.response({ok:false,status:'REJECTED',error:'NOT_AUTHORIZED_OR_INVALID_REFERENCE'});
   const found=this.negative||this.outcomes.get(input.target_request_id),r=found?historical(found):null;
   if(r&&this.mode==='wrong-identity')r.job_id='f37c93aa-d891-4691-a832-c1b275dd020d';
   return this.response({ok:true,action:'lookup_receipt',job_id:input.job_id,target_request_id:input.target_request_id,target_action:found?'create':null,found:Boolean(found),receipt:r,current_reuse_authorized:false,automatic_retry:false});
  }
  if(!this.jobExists)return this.response({ok:false,status:'REJECTED',error:'NOT_AUTHORIZED_OR_INVALID_REFERENCE',current_reuse_authorized:false,automatic_retry:false});
  if(action==='reconcile'){
   const found=this.outcomes.get(input.target_request_id),r={...common,ok:true,status:'RECORDED',pending:false,next_step_id:'produce',source_sha256:HASH,outcome_known:Boolean(found),worker_reexecuted:false,reconciled_outcome:found?historical(found):null};this.outcomes.set(input.request_id,r);return this.response(r);
  }
  if(action==='receipt'){const r=this.outcomes.get(input.target_request_id);return this.response({...common,ok:true,target_request_id:input.target_request_id,found:Boolean(r),receipt:r?historical(r):null});}
  throw Error('Unexpected action '+action);
 }
}
async function run(source){
 const results=[];
 async function test(id,mode,assertion){
  const w=new World(source,mode),t=w.tab();t.$('mandate').value='Synthetic bootstrap only';t.$('requirements').value='Keep rows';t.$('source-csv').value=CSV;
  let passed=false,reason='';
  try{await t.$('job-form').dispatch('submit',{preventDefault(){}});await assertion(w,t);passed=true;}catch(e){reason=e.message;}
  const s=w.state();results.push({id,mode,passed,reason,calls:w.calls,pending_uuid:s.pending?.intent?.input?.request_id??null,create_rejected:s.create_rejected===true,rejected_count:(s.rejected_intents||[]).length,uuid_count:w.uuidCount,worker_calls:w.calls.filter(x=>x.action==='produce').length,message:t.$('message').textContent});
 }
 await test('B01','delivered',async(w,t)=>{assert.equal(w.state().pending,null);assert.equal(w.state().create_rejected,true);assert.equal(w.calls.length,1);});
 await test('B02','failure-lost',async(w,t)=>{await t.click('reconcile');assert.equal(w.state().pending,null);assert.equal(w.state().create_rejected,true);assert.equal(w.calls.filter(x=>x.action==='create').length,1);assert.equal(w.calls.filter(x=>x.action==='reconcile').length,0);assert.equal(w.state().rejected_intents[0].proof_origin,'DURABLE_SERVER_RECEIPT');assert.ok(!w.state().completion);});
 await test('B03','success-lost',async(w,t)=>{await t.click('reconcile');assert.equal(w.state().pending,null);assert.equal(w.state().create_rejected===true,false);assert.equal(w.calls.filter(x=>x.action==='create').length,1);assert.equal(w.calls.filter(x=>x.action==='produce').length,0);assert.ok(!w.state().completion);});
 await test('B04','ambiguous',async(w,t)=>{const id=w.state().pending.intent.input.request_id;await t.click('reconcile');assert.equal(w.state().pending.intent.input.request_id,id);assert.equal((w.state().rejected_intents||[]).length,0);assert.equal(w.calls.filter(x=>x.action==='create').length,1);});
 await test('B05','wrong-identity',async(w,t)=>{const id=w.state().pending.intent.input.request_id;await t.click('reconcile');assert.equal(w.state().pending.intent.input.request_id,id);assert.equal((w.state().rejected_intents||[]).length,0);});
 await test('B06','lookup-lost',async(w,t)=>{const id=w.state().pending.intent.input.request_id,n=w.uuidCount;await t.click('reconcile');assert.equal(w.state().pending.intent.input.request_id,id);const b=w.tab('Reloaded');await b.click('reconcile');assert.equal(w.state().pending,null);assert.equal(w.state().create_rejected,true);assert.equal(w.uuidCount,n);assert.equal(w.calls.filter(x=>x.action==='create').length,1);assert.equal(w.calls.filter(x=>x.action==='reconcile').length,0);});
 return {schema:'SOL_CREATE_RECOVERY_MATCHED_UI/v1',observed_at:new Date().toISOString(),source,hashes:Object.fromEntries(['app.js','intent-slot.js'].map(n=>[n,crypto.createHash('sha256').update(fs.readFileSync(path.join(source,n))).digest('hex')])),fixture_sha256:crypto.createHash('sha256').update(fixtureBody).digest('hex'),passed:results.filter(r=>r.passed).length,cases:results.length,results,scope:'SAME_SYNTHETIC_SERVER_MODEL_DOM_LOCKS_STORAGE; not live SQL or user study; baseline B02/B06 intentionally expose missing recoverability',not_executed:['B07_SQL_DEDUP_AND_CHANGED_PAYLOAD']};
}
if(require.main===module){const [source,receipt]=process.argv.slice(2);if(!source||!receipt||fs.existsSync(receipt))throw Error('new destination required');run(source).then(r=>{fs.writeFileSync(receipt,JSON.stringify(r,null,2)+'\n');console.log(JSON.stringify({passed:r.passed,cases:r.cases,results:r.results.map(x=>({id:x.id,passed:x.passed,reason:x.reason}))}));});}
module.exports={run};
