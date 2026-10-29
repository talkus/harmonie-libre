import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {bindSources} from '../bind-sources.mjs';
import {inspect,stable} from '../verify.mjs';
const hash=x=>createHash('sha256').update(x).digest('hex');
const bytes=Buffer.from('synthetic-public-source-bytes');
function journal(source={}){
 const base={id:'s1',name:'synthetic',sourceRef:'fixture:source-1',falsifier:'different bytes',context:'ctx:1',sha256:hash(bytes),bytes:bytes.byteLength,reading:'OCTETS_HACHÉS',proof:'LOCAL_BYTES_ONLY',kRecord:'2026-10-29T01:00:00Z',tEvent:null,...source};
 const event={seq:1,type:'SOURCE',at:'2026-10-29T01:00:01Z',context:'ctx:1',data:base,prev:'0'.repeat(64)};
 return {schema:'VIGIE-V1',events:[{...event,hash:hash(stable(event))}]};
}
const file=(x=bytes)=>({id:'s1',sourceRef:'fixture:source-1',bytes:x});
test('octets effectivement relus: concordance non authentifiante',()=>{
 const d=journal(),r=bindSources(d,[file()]);assert.equal(r.ok,true);assert.equal(r.code,'CONCORDANCE_OCTETS_NON_AUTHENTIFIANTE');assert.equal(r.authenticity,'NON_ETABLIE');assert.equal(r.authorization,'NOT_ASSESSED');
});
test('étiquette OCTETS_HACHÉS seule: inspect la croit mais le témoin la réfute',()=>{
 const d=journal({sha256:'a'.repeat(64)});assert.equal(inspect(d).ok,true);
 assert.equal(bindSources(d,[file()]).code,'SOURCE_EMPREINTE_DIFFERENTE');
});
test('une substitution d octets est rejetée',()=>assert.equal(bindSources(journal(),[file(Buffer.from('modified'))]).code,'SOURCE_TAILLE_DIFFERENTE'));
test('même taille et autre contenu est rejeté',()=>assert.equal(bindSources(journal(),[file(Buffer.from('X'.repeat(bytes.byteLength)))]).code,'SOURCE_EMPREINTE_DIFFERENTE'));
test('source manquante',()=>assert.equal(bindSources(journal(),[]).code,'NOMBRE_SOURCES_INCOHERENT'));
test('source de trop',()=>assert.equal(bindSources(journal(),[file(),{id:'s2',sourceRef:'x',bytes}]).code,'NOMBRE_SOURCES_INCOHERENT'));
test('référence située erronée',()=>assert.equal(bindSources(journal(),[{...file(),sourceRef:'drive:un-autre-fichier'}]).code,'SOURCE_REFERENCE_DIFFERENTE'));
test('doublon de source',()=>assert.equal(bindSources(journal(),[file(),file()]).code,'LIEN_DUPLIQUE'));
test('type d octets illégitime',()=>assert.equal(bindSources(journal(),[{...file(),bytes:'synthetic-public-source-bytes'}]).code,'LIEN_INVALIDE'));
test('vrai fichier et faux journal: refuse avant de considérer octets',()=>{
 const d=journal();d.events[0].data.bytes+=1;
 assert.equal(bindSources(d,[file()]).code,'JOURNAL_EMPREINTE_INVALIDE');
});
test('pas de source: ne certifie pas le vide',()=>assert.equal(bindSources({schema:'VIGIE-V1',events:[]},[]).code,'SOURCES_ABSENTES'));
test('système ne certifie jamais source ou identité malgré concordance',()=>{
 const r=bindSources(journal(),[file()]);assert.equal(r.identity,'NON_VERIFIEE');assert.equal(r.canon,'NON_ADOPTE');assert.equal(r.modelAuthority,'none');
});
