const test = require('node:test');
const assert = require('node:assert/strict');
const { appendVerified, validateReadback, samePayload } = require('../bridge-write-protocol.js');

const OWNER='11111111-1111-4111-8111-111111111111';
const ID='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa';
const HASH='a'.repeat(64);
const HEAD='b'.repeat(64);
const input={event_type:'OBSERVATION',claim_key:'sol.version.active',body:'candidate, not deployed',
 source_uri:'https://example.org/source',source_kind:'PRIMARY',asserted_evidence:'SOURCE_LINKED',relates_to:null};

function fixture(opts={}) {
 let saved=null,writes=0,reads=0,stored=[];
 const store={get:()=>saved,set:v=>{saved=v;},clear:()=>{saved=null;}};
 const row={...input,idempotency_key:ID,event_id:ID,owner_id:OWNER,seq:3,event_hash:HASH};
 const readByKey=async key =>{reads++;assert.equal(key,ID);return stored;};
 const write=async payload=>{
   writes++;assert.equal(payload.idempotency_key,ID);
   if(opts.noop){if(opts.timeout)throw Error('network timeout');return;}
   stored=[{...row,...(opts.alteredRow||{})}];
   if(opts.timeout)throw Error('network timeout');
 };
 const verify=async ()=>opts.verify || {ok:true,checked:3,head_hash:HEAD};
 const run=(p=input,fingerprint='fp')=>appendVerified({payload:p,owner:OWNER,intentStore:store,
    readByKey,write,verify,uuid:()=>ID,fingerprint});
 return {run,store,stats:()=>({saved,writes,reads,stored}),setRows:r=>{stored=r;}};
}

test('confirmed write requires exact same-intent provider re-read + full-chain verification',async()=>{
 const f=fixture();const receipt=await f.run();
 assert.equal(receipt.seq,3);assert.equal(f.stats().writes,1);
 assert.equal(f.stats().reads,2);assert.equal(f.stats().saved,null);
});
test('timeout AFTER COMMIT reconciles same idempotency key without duplicate write',async()=>{
 const f=fixture({timeout:true});const receipt=await f.run();
 assert.equal(receipt.seq,3);assert.equal(f.stats().writes,1);
 assert.equal(f.stats().saved,null);
});
test('HTTP success with no durable row is NOT success and intent remains pending',async()=>{
 const f=fixture({noop:true});
 await assert.rejects(()=>f.run(),/READBACK_ABSENT_OR_AMBIGUOUS/);
 assert.equal(f.stats().saved.id,ID);
});
test('unconfirmed timeout preserves intent for same-key retry',async()=>{
 const f=fixture({noop:true,timeout:true});
 await assert.rejects(()=>f.run(),/WRITE_UNCONFIRMED_RETRY_SAME_INTENT/);
 assert.equal(f.stats().saved.id,ID);
 await assert.rejects(()=>f.run(),/READBACK_ABSENT_OR_AMBIGUOUS/);
 assert.equal(f.stats().writes,2);assert.equal(f.stats().saved.id,ID);
});
test('changing fields with an outstanding attempt refuses rather than rekeys',async()=>{
 const f=fixture({noop:true,timeout:true});await assert.rejects(()=>f.run());
 await assert.rejects(()=>f.run({...input,body:'changed'},'other fingerprint'),/UNRESOLVED_PREVIOUS_INTENT/);
 assert.equal(f.stats().writes,1);
});
test('existing matching event is read without a new POST',async()=>{
 const f=fixture();f.store.set({owner:OWNER,id:ID,fingerprint:'fp'});
 f.setRows([{...input,idempotency_key:ID,event_id:ID,owner_id:OWNER,seq:3,event_hash:HASH}]);
 const result=await f.run();
 assert.equal(f.stats().writes,0);assert.equal(result.duplicate_prevented,true);
});
test('cross-owner receipt fails closed',async()=>{
 const f=fixture({alteredRow:{owner_id:'22222222-2222-4222-8222-222222222222'}});
 await assert.rejects(()=>f.run(),/READBACK_MISMATCH/);
 assert.equal(f.stats().saved.id,ID);
});
test('wrong body receipt fails closed',async()=>{
 const f=fixture({alteredRow:{body:'fabricated success'}});
 await assert.rejects(()=>f.run(),/READBACK_MISMATCH/);
});
test('invalid chain fails closed after matching provider row',async()=>{
 const f=fixture({verify:{ok:false,checked:2,head_hash:HEAD}});
 await assert.rejects(()=>f.run(),/CHAIN_NOT_VERIFIED/);
 assert.equal(f.stats().saved.id,ID);
});
test('fake chain verification without head fails closed',async()=>{
 const f=fixture({verify:{ok:true,checked:3}});
 await assert.rejects(()=>f.run(),/CHAIN_NOT_VERIFIED/);
});
test('unverifiable hash or row mismatch not accepted',()=>{
 assert.throws(()=>validateReadback({...input,idempotency_key:ID},
  [{...input,idempotency_key:ID,owner_id:OWNER,seq:1,event_hash:'fake'}],OWNER,
  {ok:true,checked:1,head_hash:HEAD}),/READBACK_MISMATCH/);
 assert.equal(samePayload(input,{...input,body:'bad'}),false);
});
