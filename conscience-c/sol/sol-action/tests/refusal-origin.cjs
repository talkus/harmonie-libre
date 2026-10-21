'use strict';
const fs=require('node:fs'),assert=require('node:assert/strict'),path=require('node:path');
const h=require(path.resolve(process.argv[2]));
const input={job_id:'10000000-0000-4000-8000-000000000001',request_id:'10000000-0000-4000-8000-000000000002'};
const r={ok:false,status:'REJECTED',action:'create',...input,effect:'NONE_SQL_TRANSACTION_ROLLED_BACK',effect_scope:'CONTROLLED_CORE_DISPATCH_SUBTRANSACTION_ONLY',core_effect_scope:'THIS_RPC_SQL_TRANSACTION_ONLY',business_effect:'NONE_CORE_ACTION_ROLLED_BACK',terminal:true,durable_refusal:true,worker_reexecuted:false,current_reuse_authorized:false,automatic_retry:false,receipt_kind:'CONTROLLED_CREATION_REFUSAL',receipt_recording_effect:'APPEND_ONLY_CREATION_GUARD_RECEIPT_RECORDED'};
const results=[];function test(name,f){f();results.push({name,passed:true});}
test('creation exact new origin accepted',()=>assert.equal(h.controlledRefusal({action:'create',input},r),true));
for(const action of ['verify','complete'])test('new origin forbidden for '+action,()=>assert.equal(h.controlledRefusal({action,input},{...r,action}),false));
test('mixed old kind new origin refused',()=>assert.equal(h.controlledRefusal({action:'create',input},{...r,receipt_kind:'CONTROLLED_REFUSAL'}),false));
test('mixed new kind old origin refused',()=>assert.equal(h.controlledRefusal({action:'create',input},{...r,receipt_recording_effect:'APPEND_ONLY_BRIDGE_RECEIPT_RECORDED'}),false));
test('historical new origin remains historical',()=>assert.equal(h.controlledRefusal({action:'create',input},{...r,status:'HISTORICAL_NOT_CURRENT',historical_status:'REJECTED',needs_current_revalidation:true},true),true));
test('historical requires revalidation marker',()=>assert.equal(h.controlledRefusal({action:'create',input},{...r,status:'HISTORICAL_NOT_CURRENT',historical_status:'REJECTED'},true),false));
test('legacy origin remains accepted',()=>assert.equal(h.controlledRefusal({action:'verify',input},{...r,action:'verify',receipt_kind:'CONTROLLED_REFUSAL',receipt_recording_effect:'APPEND_ONLY_BRIDGE_RECEIPT_RECORDED'}),true));
if(fs.existsSync(process.argv[3]))throw Error('new receipt path required');fs.writeFileSync(process.argv[3],JSON.stringify({schema:'SOL_RECEIPT_ORIGIN_TEST/v1',results,passed:results.length},null,2)+'\n');console.log(JSON.stringify({passed:results.length}));
