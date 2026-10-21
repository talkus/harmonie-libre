'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const frozen=path.resolve('work/refus-reprise-audit-20261021/recovery-probe.cjs');
const fixture={exports:{}};
new Function('require','module','__dirname',fs.readFileSync(frozen,'utf8')+'\nmodule.exports.World=World;')(require,fixture,path.dirname(frozen));
class CreateWorld extends fixture.exports.World {
 async fetch(url,init) {
  if(url==='/provider-observation.json')return this.response(null);
  const {action,input}=JSON.parse(init.body);this.calls.push({action,request_id:input.request_id,job_id:input.job_id});
  assert.equal(action,'create');
  if(this.mode==='lost')throw new Error('Controlled reply absent after SQL rollback');
  const r={ok:false,status:'REJECTED',action,job_id:input.job_id,request_id:input.request_id,error:'CSV_HEADER',sqlstate:'P0001',effect:'NONE_SQL_TRANSACTION_ROLLED_BACK',effect_scope:'THIS_RPC_SQL_TRANSACTION_ONLY',automatic_retry:false,current_reuse_authorized:false};
  if(this.mode==='wrong_identity')r.request_id='90000000-0000-4000-8000-000000000009';
  if(this.mode==='history'){r.status='HISTORICAL_NOT_CURRENT';r.historical_status='REJECTED';}
  return this.response(r);
 }
}
async function exercise(source,mode) {
 const w=new CreateWorld(source,mode);w.store.delete('sol-action-session-v1');const t=w.tab();
 t.$('mandate').value='Synthetic invalid create admission';t.$('requirements').value='Exact cents';t.$('source-csv').value='wrong,currency,amount\none,EUR,0.10\n';
 await t.$('job-form').dispatch('submit',{preventDefault(){}});
 return {w,t,state:w.state()};
}
async function run(source,receiptPath) {
 assert.ok(!fs.existsSync(receiptPath),'New receipt path required');const results=[];
 for(const mode of ['delivered','lost','wrong_identity','history']) {
  try {
   const {w,state}=await exercise(source,mode);assert.equal(w.calls.length,1,'No automatic recovery or retry');
   if(mode==='delivered'){
    assert.equal(state.pending,null);assert.equal(state.create_rejected,true);assert.equal(state.adaptation_draft,true);
    assert.equal(state.rejected_intents.length,1);assert.equal(state.rejected_intents[0].proof_origin,'LIVE_CREATE_RPC_RESPONSE_ONLY');
    assert.equal(state.rejected_intents[0].response.durable_refusal,undefined);
   }else{
    assert.ok(state.pending);assert.notEqual(state.adaptation_draft,true);assert.equal((state.rejected_intents||[]).length,0);
    const bytes=w.store.get('sol-action-session-v1');w.tab();assert.equal(w.store.get('sol-action-session-v1'),bytes);assert.equal(w.calls.length,1);
   }
   results.push({case:mode,status:'PASS'});
  }catch(e){results.push({case:mode,status:'FAIL',error:e.message});}
 }
 const r={schema:'SOL_LIVE_CREATE_REFUSAL_REGRESSION/v1',observed_at_utc:new Date().toISOString(),source,source_sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(source,'app.js'))).digest('hex'),test_source_sha256:crypto.createHash('sha256').update(fs.readFileSync(__filename)).digest('hex'),fixture_source_sha256:crypto.createHash('sha256').update(fs.readFileSync(frozen)).digest('hex'),tests:results.length,passed:results.filter(x=>x.status==='PASS').length,results,scope:'Synthetic DOM/storage/Web Locks/transport only. Direct delivered core rollback distinct from durable receipt; no PostgreSQL/provider/external mutation.'};
 fs.writeFileSync(receiptPath,JSON.stringify(r,null,2)+'\n');return r;
}
if(require.main===module)run(process.argv[2],process.argv[3]).then(r=>{console.log(JSON.stringify(r));if(r.passed!==r.tests)process.exitCode=1;}).catch(e=>{console.error(e);process.exitCode=1;});
module.exports={run};

