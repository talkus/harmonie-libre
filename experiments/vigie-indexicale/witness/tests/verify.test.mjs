import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash,generateKeyPairSync,sign} from 'node:crypto';
import {inspect,stable} from '../verify.mjs';
const H=x=>createHash('sha256').update(x).digest('hex');
const genesis='0'.repeat(64);
function append(a,type,data,ctx='ctx-1',at='2026-10-28T10:00:01Z'){
  const envelope={seq:a.length+1,type,at,context:ctx,data,prev:a.length?a.at(-1).hash:genesis};
  a.push({...envelope,hash:H(stable(envelope))});return a;
}
function seed(){const e=[];append(e,'SOURCE',{id:'src1',name:'local-file',sourceRef:'local:receipt',falsifier:'octets différents',context:'ctx-1',sha256:H('bytes'),bytes:5,reading:'OCTETS_HACHÉS',proof:'LOCAL_BYTES_ONLY',kRecord:'2026-10-28T10:00:00Z',tEvent:null});return {schema:'VIGIE-V1',events:e};}
function change(doc,type,data,ctx='ctx-1'){append(doc.events,type,data,ctx);return doc;}
function retip(doc){let prev=genesis;for(const e of doc.events){e.prev=prev;const {hash,...envelope}=e;e.hash=H(stable(envelope));prev=e.hash;}return doc;}
const q={id:'q1',sourceId:'src1',recipient:'témoin externe',cost:'perte de provenance',gap:'la provenance est inconnue',context:'ctx-1',status:'GAP_MARKED'};
const claimFields={id:'c1',sourceId:'src1',statement:'assertion falsifiable',falsifier:'preuve inverse',subject:'sujet-1',proposer:'proposant-1',context:'ctx-1',epistemic:'E0',authorization:'NOT_ASSESSED',execution:'NOT_PERFORMED'};
function withClaim(){const d=seed();const f={sourceId:'src1',sourceHash:H('bytes'),statement:claimFields.statement,falsifier:claimFields.falsifier,subject:claimFields.subject,proposer:claimFields.proposer,context:'ctx-1'};change(d,'CLAIM',{...claimFields,statementHash:H(stable(f))});return d;}
test('source minimale et pointeur local ne certifient pas le réel',()=>{const r=inspect(seed());assert.equal(r.ok,true);assert.equal(r.identity,'NON_VERIFIEE');assert.equal(r.modelAuthority,'none');});
test('empreinte altérée est rejetée',()=>{const d=seed();d.events[0].data.bytes=8;assert.equal(inspect(d).code,'EMPREINTE_INVALIDE');});
test('faux E_PLUS rehashé est rejeté',()=>{const d=withClaim();d.events[1].data.epistemic='E_PLUS';retip(d);assert.equal(inspect(d).code,'ASSERTION_AUTORITE');});
test('réponse sans question rehashée rejetée',()=>{const d=seed();change(d,'ANSWER',{questionId:'absent',respondent:'témoin externe'});assert.equal(inspect(d).code,'REPONSE_INVALIDE');});
test('auto-adresse est rejetée',()=>{const d=seed();change(d,'QUESTION',{...q,recipient:'SELF'});assert.equal(inspect(d).code,'QUESTION_INVALIDE');});
test('vide marqué, sans faux contenu',()=>{const d=seed();change(d,'QUESTION',q);assert.equal(inspect(d).ok,true);});
test('un ancien contexte ne vaut pas dans le nouveau',()=>{const d=seed();change(d,'CONTEXT',{prior:'ctx-1',context:'ctx-2'},'ctx-2');change(d,'QUESTION',q);assert.equal(inspect(d).code,'INDEX_PERIME');});
test('un reçu indépendant non concordant est détecté',()=>{const d=seed();assert.equal(inspect(d,{tip:genesis,count:1,context:'ctx-1'}).code,'RECU_NON_CONCORDANT');});
test('reçu concordant ne certifie pas le référent',()=>{const d=seed(),tip=d.events.at(-1).hash;assert.equal(inspect(d,{tip,count:1,context:'ctx-1'}).code,'CONCORDANCE_NON_AUTHENTIFIANTE');});
test('revue avec signature valide ne certifie pas identité',()=>{
 const d=withClaim(); const {publicKey,privateKey}=generateKeyPairSync('ed25519');const raw=publicKey.export({format:'der',type:'spki'}).subarray(-32).toString('base64');
 change(d,'VERIFIER',{id:'tiers-A',keyB64:raw,context:'ctx-1',scope:'CLÉ_PINNÉE_LOCALEMENT_IDENTITÉ_NON_PROUVÉE'});
 const c=d.events[1].data;const message=stable({schema:'VIGIE-ATTEST-V1',claimId:'c1',context:'ctx-1',statementHash:c.statementHash,sourceHash:H('bytes'),decision:'SATISFIED',verifierId:'tiers-A'});
 const sig=sign(null,Buffer.from(message),privateKey).toString('base64');const review={claimId:'c1',verifierId:'tiers-A',decision:'SATISFIED',signatureB64:sig,sourceHash:H('bytes'),statementHash:c.statementHash,context:'ctx-1',status:'SIGNATURE_VALIDE_CLÉ_LOCALE_IDENTITÉ_NON_VÉRIFIÉE'};
 change(d,'REVIEW',review);const ok=inspect(d);assert.equal(ok.ok,true);assert.equal(ok.signatures_valides_cle_locale,1);assert.equal(ok.identity,'NON_VERIFIEE');
 d.events.at(-1).data.signatureB64=Buffer.alloc(64).toString('base64');retip(d);assert.equal(inspect(d).code,'SIGNATURE_INVALIDE');
});
test('le destinataire ne peut pas s attribuer une vérification',()=>{const d=withClaim();const {publicKey}=generateKeyPairSync('ed25519');change(d,'VERIFIER',{id:'sujet-1',keyB64:publicKey.export({format:'der',type:'spki'}).subarray(-32).toString('base64'),context:'ctx-1',scope:'CLÉ_PINNÉE_LOCALEMENT_IDENTITÉ_NON_PROUVÉE'});change(d,'REVIEW',{claimId:'c1',verifierId:'sujet-1'});assert.equal(inspect(d).code,'AUTO_EVALUATION_OU_REVUE_INCONNUE');});

// Compatibility contract: journal emitted by the actual Netlify v0.2 engine,
// not constructed with the witness's own append() fixture utility.
const fixtureBase=new URL('../../fixtures/',import.meta.url);
test('interop réelle: export moteur v0.2 + reçu synthétique',async()=>{
 const {readFileSync}=await import('node:fs');
 const journal=JSON.parse(readFileSync(new URL('journal-synthetique-v02.json',fixtureBase),'utf8'));
 const receipt=JSON.parse(readFileSync(new URL('recu-synthetique-v02.json',fixtureBase),'utf8'));
 const r=inspect(journal,receipt);
 assert.equal(r.ok,true);assert.equal(r.code,'CONCORDANCE_NON_AUTHENTIFIANTE');
 assert.equal(r.count,6);assert.equal(r.signatures_valides_cle_locale,1);
 assert.equal(r.modelAuthority,'none');assert.equal(r.authorization,'NOT_ASSESSED');
});
test('interop adversariale: réponse falsifiée puis chaîne recalculée refusée',async()=>{
 const {readFileSync}=await import('node:fs');
 const journal=JSON.parse(readFileSync(new URL('journal-synthetique-v02.json',fixtureBase),'utf8'));
 journal.events.find(e=>e.type==='ANSWER').data.respondent='self';
 retip(journal);
 assert.equal(inspect(journal).code,'REPONSE_INVALIDE');
});
test('interop adversariale: reçu original invalide après re-hachage du journal',async()=>{
 const {readFileSync}=await import('node:fs');
 const journal=JSON.parse(readFileSync(new URL('journal-synthetique-v02.json',fixtureBase),'utf8'));
 const receipt=JSON.parse(readFileSync(new URL('recu-synthetique-v02.json',fixtureBase),'utf8'));
 journal.events.find(e=>e.type==='SOURCE').data.sourceRef='fixture:une-autre-source';
 retip(journal);
 assert.equal(inspect(journal).ok,true); // rehashing can preserve syntactic/semantic validity
 assert.equal(inspect(journal,receipt).code,'RECU_NON_CONCORDANT');
});
test('base64url non capitonné admis comme dans le moteur du navigateur',async()=>{
 const {readFileSync}=await import('node:fs');
 const journal=JSON.parse(readFileSync(new URL('journal-synthetique-v02.json',fixtureBase),'utf8'));
 for(const ev of journal.events){
  if(ev.type==='VERIFIER')ev.data.keyB64=ev.data.keyB64.replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
  if(ev.type==='REVIEW')ev.data.signatureB64=ev.data.signatureB64.replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
 }
 retip(journal);
 assert.equal(inspect(journal).ok,true);
});
