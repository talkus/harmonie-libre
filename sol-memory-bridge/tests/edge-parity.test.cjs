const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const base=require('node:path').join(__dirname,'..');
const content=fs.readFileSync(require('node:path').join(base,'supabase-edge/index.ts'),'utf8');
const boundary=content.indexOf('Deno.serve(');
test('Edge source parses as JavaScript and does not expose data as implicit authority',()=>{
 assert.ok(boundary>0);
 assert.doesNotThrow(()=>new vm.Script(content,{filename:'supabase-edge/index.ts'}));
});
test('deployed Edge bundle uses the identical separately tested write protocol',()=>{
 const context={};
 vm.runInNewContext(content.slice(0,boundary)+'\nthis.__bundled={PAGE,PROTOCOL_JS};',context);
 const expected=fs.readFileSync(require('node:path').join(base,'bridge-write-protocol.js'),'utf8');
 assert.equal(context.__bundled.PROTOCOL_JS,expected);
 const html=context.__bundled.PAGE;
 assert.match(html,/SolBridgeProtocol\.appendVerified/);
 assert.match(html,/bridge-write-protocol\.js/);
 assert.match(html,/idempotency_key=eq\./);
 assert.match(html,/CONFIRMÉ par relecture/);
 assert.doesNotMatch(html,/status\("Événement ajouté/);
});
test('Gate cannot treat frontend /healthz as database verification',()=>{
 assert.match(content,/database_check/);
 assert.match(content,/NOT_RUN/);
 assert.match(content,/CHAIN_NOT_VERIFIED/);
});
