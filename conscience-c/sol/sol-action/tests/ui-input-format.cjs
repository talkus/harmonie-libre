'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const source=path.resolve(process.argv[2]),receipt=process.argv[3];assert.ok(source&&receipt&&!fs.existsSync(receipt),'Explicit source and new receipt');
const h=require(source),base='id,currency,amount\none,EUR,0.10\n',results=[];
function check(name,fn){try{fn();results.push({name,status:'PASS'});}catch(e){results.push({name,status:'FAIL',error:e.message});}}
check('format-only valid LF',()=>{const r=h.validateCsv(base);assert.equal(r.ok,true);assert.equal(r.scope,'INPUT_FORMAT_ONLY');assert.equal(r.rows,1);assert.equal(r.current_reuse_authorized,undefined);assert.equal(r.totals,undefined);});
check('valid quoted header and CRLF',()=>assert.equal(h.validateCsv('"id","currency","amount"\r\n"one","EUR","+1.00"\r\n').ok,true));
for(const [name,csv,code,line] of [
 ['header','wrong,currency,amount\none,EUR,0.10\n','CSV_HEADER',1],
 ['columns','id,currency,amount\none,EUR\n','CSV_COLUMNS',2],
 ['currency','id,currency,amount\none,eur,1.00\n','CSV_CURRENCY',2],
 ['amount','id,currency,amount\none,EUR,1.001\n','CSV_AMOUNT',2],
 ['ID','id,currency,amount\n#,EUR,1.00\n','CSV_ID',2],
 ['duplicate','id,currency,amount\none,EUR,1.00\none,EUR,2.00\n','CSV_DUPLICATE_ID',3],
 ['unclosed quote','id,currency,amount\none,"EUR,1.00\n','CSV_QUOTING',2],
 ['quote inside unquoted','id,currency,amount\non"e,EUR,1.00\n','CSV_QUOTING',2],
 ['lone CR separator','id,currency,amount\rone,EUR,1.00\n','CSV_LINE_ENDING',1],
 ['quoted final LF currency','id,currency,amount\none,"EUR\n",1.00\n','CSV_CURRENCY',2],
 ['quoted final CR currency','id,currency,amount\none,"EUR\r",1.00\n','CSV_CURRENCY',2],
 ['quoted final LF amount','id,currency,amount\none,EUR,"1.00\n"\n','CSV_AMOUNT',2],
 ['quoted final CR amount','id,currency,amount\none,EUR,"1.00\r"\n','CSV_AMOUNT',2],
 ['quoted final LF identifier','id,currency,amount\n"one\n",EUR,1.00\n','CSV_ID',2]
])check(name,()=>{const r=h.validateCsv(csv);assert.equal(r.ok,false);assert.equal(r.errors[0].code,code);assert.equal(r.errors[0].line,line);});
check('UTF8 byte cap',()=>assert.equal(h.validateCsv('é'.repeat(16385)).errors[0].code,'CSV_SIZE'));
check('BOM rejected',()=>assert.equal(h.validateCsv('\ufeff'+base).errors[0].code,'CSV_ENCODING'));
check('max 500 data records',()=>{assert.equal(h.validateCsv('id,currency,amount\n'+Array.from({length:500},(_,i)=>'r'+i+',EUR,0.01\n').join('')).ok,true);assert.equal(h.validateCsv('id,currency,amount\n'+Array.from({length:501},(_,i)=>'r'+i+',EUR,0.01\n').join('')).errors[0].code,'CSV_ROWS');});
check('mandate and requirements get own diagnostics',()=>{const r=h.validateCreation('',[],base);assert.equal(r.ok,false);assert.deepEqual(r.errors.map(x=>x.field),['mandate','requirements']);});
for(const code of ['__proto__','constructor','toString','<script>secret</script>',{toString:1},null,17])check('unknown/poison code '+JSON.stringify(code),()=>assert.equal(h.diagnosticFor({error:code}),null));
check('known server alias maps field without inventing line',()=>{const r=h.diagnosticFor({error:'REQUIREMENT_TEXT',line:88,details:'secret'});assert.equal(r.field,'requirements');assert.equal(r.line,null);assert.equal(r.message.includes('secret'),false);});
check('result strings also require full match',()=>assert.equal(h.validResult({source_sha256:'a'.repeat(64),rows:1,row_ids:['one'],totals:[{currency:'EUR\n',amount:'1.00'}]}),false));
const r={schema:'SOL_UI_INPUT_FORMAT_CHECKS/v1',scope:'Local string parsing and allowlisted diagnostics only; no totals or proof authority, no remote calls',source_sha256:crypto.createHash('sha256').update(fs.readFileSync(source)).digest('hex'),test_sha256:crypto.createHash('sha256').update(fs.readFileSync(__filename)).digest('hex'),tests:results.length,passed:results.filter(x=>x.status==='PASS').length,results};fs.writeFileSync(receipt,JSON.stringify(r,null,2)+'\n');console.log(JSON.stringify(r));if(r.passed!==r.tests)process.exitCode=1;

