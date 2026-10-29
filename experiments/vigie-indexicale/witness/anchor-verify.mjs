/**
 * Vigie Indexicale — quorum de clés pré-épinglées, sans auto-certification.
 * La signature garantit la concordance avec les clés fournies en dehors du journal.
 * Elle NE prouve PAS l'indépendance réelle de leurs détenteurs, leur identité ou la date.
 * Ce module ne modifie jamais le journal. Aucun réseau.
 */
import { createHash, createPublicKey, verify as edVerify } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { inspect, stable } from './verify.mjs';

const H = s => createHash('sha256').update(s).digest('hex');
const HEX64 = s => typeof s === 'string' && /^[0-9a-f]{64}$/.test(s);
const text = s => typeof s === 'string' && s.trim() !== '';
const error = c => { throw Object.assign(new Error(c), { code:c }); };
function bytes(s, n){
  if(typeof s!=='string' || !s || !/^(?:[A-Za-z0-9+/_-]+)(?:={0,2})$/.test(s) || (/[+\/]/.test(s) && /[-_]/.test(s)))error('BASE64_INVALIDE');
  const v=s.replace(/-/g,'+').replace(/_/g,'/').replace(/=+$/,'');
  if(v.length%4===1)error('BASE64_INVALIDE');
  const b=Buffer.from(v,'base64');
  if(b.length!==n || b.toString('base64').replace(/=+$/,'')!==v)error('TAILLE_OU_BASE64_INVALIDE');
  return b;
}
function spki(key){return createPublicKey({key:Buffer.concat([Buffer.from('302a300506032b6570032100','hex'),key]),format:'der',type:'spki'});}
function verifySeal(anchor,trust,producerKeys){
  if(anchor?.schema!=='VIGIE-ANCHOR-V1' || !Array.isArray(anchor.signatures))error('FORMAT_ANCRE');
  if(trust?.schema!=='VIGIE-TRUST-V1' || !Array.isArray(trust.pins) || !Number.isSafeInteger(trust.threshold) || trust.threshold<2)error('QUORUM_NON_CONFORME');
  const pins=new Map(), pubkeys=new Set();
  for(const p of trust.pins){
    if(!text(p?.id) || p.role!=='WITNESS' || pins.has(p.id))error('TRUST_PINS_INVALIDES');
    const k=bytes(p.keyB64,32),hex=k.toString('hex');
    if(pubkeys.has(hex))error('TRUST_CLES_DUPLIQUEES');
    if(producerKeys.has(hex))error('AUTO_TEMOIN_CLE');
    pubkeys.add(hex);pins.set(p.id,k);
  }
  if(trust.threshold>pins.size)error('QUORUM_IMPOSSIBLE');
  const cp=anchor.checkpoint;
  if(cp?.schema!=='VIGIE-CHECKPOINT-V1' || !HEX64(cp.tip) || !Number.isSafeInteger(cp.count) || cp.count<1 || !text(cp.context) || !Number.isSafeInteger(cp.sequence) || cp.sequence<1 || !text(cp.nonce) || cp.nonce.length<16 || !text(cp.claimedAt) || !Number.isFinite(Date.parse(cp.claimedAt)) || cp.scope!=='CHECKPOINT_HASH_ONLY' || !(cp.previousTip===null || HEX64(cp.previousTip)))error('POINT_INVALIDE');
  if(anchor.signatures.length<trust.threshold)error('SIGNATURES_INSUFFISANTES');
  const msg=Buffer.from(stable(cp),'utf8');
  const seen=new Set(),sealed=new Set();
  for(const x of anchor.signatures){
    if(!text(x?.witnessId) || seen.has(x.witnessId))error('SIGNATURE_DUPLIQUEE');
    seen.add(x.witnessId);
    const k=pins.get(x.witnessId);
    if(!k)error('TEMOIN_NON_EPINGLE');
    if(!edVerify(null,msg,spki(k),bytes(x.signatureB64,64)))error('SIGNATURE_INVALIDE');
    sealed.add(k.toString('hex'));
  }
  if(sealed.size<trust.threshold)error('QUORUM_INSUFFISANT');
  return {cp, signerCount:sealed.size};
}

/**
 * @param {{journal:object,anchor:object,trust:object,previousAnchor?:object}} args
 * Trust must be supplied separately from journal and anchor; in-band trust is rejected.
 */
export function auditAnchored({journal,anchor,trust,previousAnchor=null}={}){
  try {
    const full=inspect(journal);
    if(!full.ok)error('JOURNAL_'+full.code);
    if(anchor===journal || trust===journal || anchor===trust || (trust!==undefined && trust!==null && trust===anchor?.trust) || Object.hasOwn(anchor??{},'trust'))error('CONFIANCE_AUTO_DECLAREE');
    const producerKeys=new Set();
    for(const e of journal.events){if(e.type==='VERIFIER')producerKeys.add(bytes(e.data.keyB64,32).toString('hex'));}
    const {cp,signerCount}=verifySeal(anchor,trust,producerKeys);
    if(cp.count>journal.events.length)error('ANCRE_FUTURE');
    const prefix={schema:'VIGIE-V1',events:journal.events.slice(0,cp.count)};
    const parsed=inspect(prefix);
    if(!parsed.ok)error('PREFIXE_'+parsed.code);
    if(!prefix.events.some(e=>e.type==='SOURCE'))error('AUCUNE_SOURCE_DANS_ANCRE');
    if(parsed.tip!==cp.tip || parsed.context!==cp.context)error('ANCRE_DIVERGENTE');
    if(Date.parse(cp.claimedAt)<Date.parse(prefix.events.at(-1).at))error('TEMPS_DECLARE_INCOHERENT');
    if(previousAnchor){
      const old=verifySeal(previousAnchor,trust,producerKeys).cp;
      if(old.count>=cp.count || old.sequence+1!==cp.sequence || cp.previousTip!==old.tip)error('CONTINUITE_NON_ETABLIE');
      if(journal.events[old.count-1]?.hash!==old.tip)error('ANCIEN_POINT_DIVERGENT');
      if(Date.parse(cp.claimedAt)<Date.parse(old.claimedAt))error('TEMPS_DECLARE_NON_MONOTONE');
    } else if(cp.sequence!==1 || cp.previousTip!==null)error('ANCRE_PRECEDENTE_MANQUANTE');
    return {ok:true,code:'CONCORDANCE_SIGNATAIRES_ET_PREFIXE',anchoredEvents:cp.count,totalEvents:full.count,unanchoredEvents:full.count-cp.count,signatures:signerCount,
      tip:cp.tip,tipCurrent:full.tip,declaredAt:cp.claimedAt,
      independentCustody:'NOT_ESTABLISHED',identity:'NOT_VERIFIED',timestampAuthenticity:'NOT_ESTABLISHED',sourceAuthenticity:'NOT_ESTABLISHED',
      epistemic:'E0',modelAuthority:'none',authorization:'NOT_ASSESSED',canon:'NOT_ADOPTED'};
  } catch(e){return {ok:false,code:e.code||'VERIFICATION_IMPOSSIBLE',epistemic:'E0',authorization:'NOT_ASSESSED',identity:'NOT_VERIFIED'};}
}
if(process.argv[1] && import.meta.url===new URL('file://'+process.argv[1]).href){
  if(process.argv.length<5 || process.argv.length>6){console.error('Usage: node anchor-verify.mjs export.json anchor.json trust-EXTERNE.json [previous-anchor.json]');process.exit(2);}
  try {
    const [j,a,t,p]=process.argv.slice(2).map(f=>f?JSON.parse(readFileSync(f,'utf8')):null);
    const report=auditAnchored({journal:j,anchor:a,trust:t,previousAnchor:p});
    console.log(JSON.stringify(report,null,2));if(!report.ok)process.exitCode=1;
  }catch(e){console.error(JSON.stringify({ok:false,code:'ERREUR_LEC_FICHIERS',message:e.message}));process.exitCode=2;}
}
