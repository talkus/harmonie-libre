/** Independent, read-only verifier for VIGIE-V1 exports. No network or model authority. */
import {createHash, createPublicKey, verify as verifyEd25519} from 'node:crypto';
import {readFileSync} from 'node:fs';

const GENESIS = '0'.repeat(64);
const TYPES = new Set(['SOURCE','QUESTION','ANSWER','CLAIM','VERIFIER','REVIEW','REFUSAL','CONTEXT']);
const SELF = new Set(['me','self','soi','moi','system','système','systeme','assistant','modèle','modele','roues','cherubs','wheels']);
const norm = x => String(x ?? '').normalize('NFKC').trim().toLocaleLowerCase('fr');
const filled = x => typeof x === 'string' && x.trim().length > 0;
const digest = x => createHash('sha256').update(x).digest('hex');
const hex64 = x => typeof x === 'string' && /^[a-f0-9]{64}$/.test(x);
export function stable(x) {
  if (x === null || typeof x !== 'object') return JSON.stringify(x);
  if (Array.isArray(x)) return '['+x.map(stable).join(',')+']';
  return '{'+Object.keys(x).sort().map(k => JSON.stringify(k)+':'+stable(x[k])).join(',')+'}';
}
const fail = (code, seq = null) => { throw Object.assign(new Error(code), {code,seq}); };
const requireThat = (ok, code, seq) => { if (!ok) fail(code,seq); };
// The browser core accepts canonical base64 and unpadded base64url (Web Crypto keys).
// Reject mixed alphabets and truncated representations instead of coercing them.
const b64 = s => {
  requireThat(typeof s === 'string' && s.length > 0 && !(/[+\/]/.test(s) && /[-_]/.test(s)),'BASE64_INVALIDE');
  const raw=s.replace(/-/g,'+').replace(/_/g,'/').replace(/=+$/,'');
  requireThat(/^[A-Za-z0-9+/]+$/.test(raw) && raw.length%4!==1 &&
    /^(?:[A-Za-z0-9+/_-]+)(?:={0,2})$/.test(s),'BASE64_INVALIDE');
  const decoded=Buffer.from(raw,'base64');
  requireThat(decoded.toString('base64').replace(/=+$/,'')===raw,'BASE64_INVALIDE');
  return decoded;
};
function verifyReview(d, cl, source, verifier, seq) {
  requireThat(d.context === cl.context && d.context === verifier.context &&
    d.sourceHash === source.sha256 && d.statementHash === cl.statementHash &&
    d.status === 'SIGNATURE_VALIDE_CLÉ_LOCALE_IDENTITÉ_NON_VÉRIFIÉE' &&
    ['SATISFIED','VIOLATED'].includes(d.decision),'REVUE_LIAISON',seq);
  const key=b64(verifier.keyB64), signature=b64(d.signatureB64);
  requireThat(key.length===32 && signature.length===64,'REVUE_TAILLE_CLÉ_SIGNATURE',seq);
  const spki=Buffer.concat([Buffer.from('302a300506032b6570032100','hex'),key]);
  const publicKey=createPublicKey({key:spki,format:'der',type:'spki'});
  const message=stable({schema:'VIGIE-ATTEST-V1',claimId:cl.id,context:cl.context,
    statementHash:cl.statementHash,sourceHash:source.sha256,decision:d.decision,verifierId:d.verifierId});
  requireThat(verifyEd25519(null,Buffer.from(message),publicKey,signature),'SIGNATURE_INVALIDE',seq);
}
export function inspect(doc,checkpoint=null) {
  try {
    requireThat(doc?.schema==='VIGIE-V1' && Array.isArray(doc.events),'FORMAT_INVALIDE');
    const events=doc.events, src=new Map(),qs=new Map(),claims=new Map(),keys=new Map(),answered=new Set(),reviewed=new Set();
    let prev=GENESIS, context=null,prevAt=-Infinity, signatures=0;
    for(let i=0;i<events.length;i++){
      const e=events[i],seq=i+1;
      requireThat(e && typeof e==='object' && !Array.isArray(e) && e.seq===seq && e.prev===prev && hex64(e.hash),'CHAINE_INVALIDE',seq);
      const {hash,...envelope}=e;
      requireThat(digest(stable(envelope))===hash,'EMPREINTE_INVALIDE',seq);
      requireThat(TYPES.has(e.type) && e.data && typeof e.data==='object' && !Array.isArray(e.data),'TYPE_INVALIDE',seq);
      requireThat(filled(e.context) && norm(e.context)!=='*','CONTEXTE_INVALIDE',seq);
      const at=Date.parse(e.at);
      requireThat(Number.isFinite(at) && at>=prevAt,'TEMPS_INVALIDE',seq); prevAt=at;
      if(context===null)context=e.context;
      const d=e.data;
      if(e.type==='CONTEXT'){
        requireThat(d.prior===context && d.context===e.context && d.context!==context,'DEPLACEMENT_CONTEXTE_INVALIDE',seq);
        context=d.context;
      } else {
        requireThat(e.context===context,'INDEX_PERIME',seq);
        if(e.type==='SOURCE'){
          requireThat(filled(d.id)&&!src.has(d.id)&&filled(d.name)&&filled(d.sourceRef)&&filled(d.falsifier)&&d.context===context&&hex64(d.sha256)&&Number.isSafeInteger(d.bytes)&&d.bytes>=0&&d.reading==='OCTETS_HACHÉS'&&d.proof==='LOCAL_BYTES_ONLY','SOURCE_NON_ETAYEE',seq);
          const k=Date.parse(d.kRecord),t=d.tEvent?Date.parse(d.tEvent):null;
          requireThat(Number.isFinite(k)&&k<=at+2000&&(t===null||(Number.isFinite(t)&&t<=k+1000)),'T_K_INVALIDE',seq);
          src.set(d.id,d);
        } else if(e.type==='QUESTION'){
          requireThat(filled(d.id)&&!qs.has(d.id)&&src.get(d.sourceId)?.context===context&&filled(d.recipient)&&!SELF.has(norm(d.recipient))&&filled(d.cost)&&d.cost.trim().length>=12&&filled(d.gap)&&d.gap.trim().length>=12&&d.status==='GAP_MARKED'&&d.context===context,'QUESTION_INVALIDE',seq);
          qs.set(d.id,d);
        } else if(e.type==='ANSWER'){
          const q=qs.get(d.questionId);
          requireThat(q?.context===context&&!answered.has(d.questionId)&&norm(d.respondent)===norm(q.recipient)&&!SELF.has(norm(d.respondent))&&filled(d.provenance)&&!SELF.has(norm(d.provenance))&&filled(d.falsifier)&&filled(d.content)&&d.priorState==='GAP_MARKED'&&d.state==='ANSWER_CLAIMED'&&d.status==='NON_AUTHENTIFIÉ','REPONSE_INVALIDE',seq);
          answered.add(d.questionId);
        } else if(e.type==='CLAIM'){
          const source=src.get(d.sourceId);
          requireThat(source?.context===context&&filled(d.id)&&!claims.has(d.id)&&filled(d.statement)&&d.statement.trim().length>8&&filled(d.falsifier)&&filled(d.subject)&&filled(d.proposer)&&d.context===context&&d.epistemic==='E0'&&d.authorization==='NOT_ASSESSED'&&d.execution==='NOT_PERFORMED','ASSERTION_AUTORITE',seq);
          const h=digest(stable({sourceId:d.sourceId,sourceHash:source.sha256,statement:d.statement,falsifier:d.falsifier,subject:d.subject,proposer:d.proposer,context:d.context}));
          requireThat(h===d.statementHash,'ASSERTION_EMPREINTE',seq); claims.set(d.id,d);
        } else if(e.type==='VERIFIER'){
          requireThat(filled(d.id)&&!keys.has(d.id)&&!SELF.has(norm(d.id))&&d.context===context&&d.scope==='CLÉ_PINNÉE_LOCALEMENT_IDENTITÉ_NON_PROUVÉE'&&b64(d.keyB64).length===32,'CLE_NON_SITUEE',seq); keys.set(d.id,d);
        } else if(e.type==='REVIEW'){
          const cl=claims.get(d.claimId),v=keys.get(d.verifierId);
          requireThat(cl&&v&&!reviewed.has(d.claimId)&&cl.context===context&&v.context===context&&!SELF.has(norm(d.verifierId))&&norm(d.verifierId)!==norm(cl.subject)&&norm(d.verifierId)!==norm(cl.proposer),'AUTO_EVALUATION_OU_REVUE_INCONNUE',seq);
          verifyReview(d,cl,src.get(cl.sourceId),v,seq);reviewed.add(d.claimId);signatures++;
        } else if(e.type==='REFUSAL')requireThat(filled(d.reason),'REFUS_MUET',seq);
      }
      prev=e.hash;
    }
    if(checkpoint){
      requireThat(hex64(checkpoint.tip)&&Number.isSafeInteger(checkpoint.count)&&filled(checkpoint.context),'RECU_INVALIDE');
      requireThat(checkpoint.tip===prev && checkpoint.count===events.length && checkpoint.context===(context??'session-01'),'RECU_NON_CONCORDANT');
    }
    return {ok:true,code:checkpoint?'CONCORDANCE_NON_AUTHENTIFIANTE':'CHAINE_SITUEE_NON_AUTHENTIFIANTE',count:events.length,tip:prev,context:context??'session-01',signatures_valides_cle_locale:signatures,identity:'NON_VERIFIEE',modelAuthority:'none',authorization:'NOT_ASSESSED',canon:'NON_ADOPTE'};
  } catch(e) {return {ok:false,code:e.code||'VERIFICATION_IMPOSSIBLE',seq:e.seq??null,message:String(e.message)};}
}
if(process.argv[1] && import.meta.url===new URL('file://'+process.argv[1]).href){
  if(process.argv.length<3 || process.argv.length>4){console.error('Usage: node verify.mjs export-vigie.json [recu-independant.json]');process.exit(2)}
  try{const doc=JSON.parse(readFileSync(process.argv[2],'utf8'));const cp=process.argv[3]?JSON.parse(readFileSync(process.argv[3],'utf8')):null;const r=inspect(doc,cp);console.log(JSON.stringify(r,null,2));if(!r.ok)process.exitCode=1;}catch(e){console.error(e.message);process.exitCode=2;}
}
