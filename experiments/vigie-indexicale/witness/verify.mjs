/** VIGIE-V1 : témoin indépendant read-only. Aucun accès Drive, réseau ou pouvoir de décision. */
import {createHash,createPublicKey,verify as verifyEd25519} from 'node:crypto';
import {readFileSync} from 'node:fs';
const ZERO='0'.repeat(64);
const TYPES=new Set(['SOURCE','QUESTION','ANSWER','CLAIM','VERIFIER','REVIEW','REFUSAL','CONTEXT']);
const SELF=new Set(['me','self','soi','moi','system','système','systeme','assistant','modèle','modele','roues','cherubs','wheels']);
const normalize=s=>String(s??'').normalize('NFKC').trim().toLocaleLowerCase('fr');
const present=s=>typeof s==='string'&&s.trim().length>0;
const hex64=s=>typeof s==='string'&&/^[a-f0-9]{64}$/.test(s);
export const stable=v=>v===null||typeof v!=='object'?JSON.stringify(v):Array.isArray(v)?'['+v.map(stable).join(',')+']':'{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+stable(v[k])).join(',')+'}';
const hash=x=>createHash('sha256').update(x).digest('hex');
const required=(v,reason,seq)=>{if(!v)throw Object.assign(new Error(reason),{code:reason,seq});};
const base64=s=>{required(typeof s==='string'&&/^[a-zA-Z0-9+/]+={0,2}$/.test(s)&&s.length%4===0,'BASE64_INVALIDE');return Buffer.from(s,'base64');};
export function inspect(doc,receipt=null){
 try{
  required(doc?.schema==='VIGIE-V1'&&Array.isArray(doc.events),'FORMAT_INVALIDE');
  const sources=new Map(),questions=new Map(),claims=new Map(),verifiers=new Map(),answered=new Set(),reviewed=new Set();
  let prev=ZERO,context=null,priorAt=-Infinity,signatures=0;
  for(let i=0;i<doc.events.length;i++){
   const e=doc.events[i],seq=i+1;
   required(e&&typeof e==='object'&&e.seq===seq&&e.prev===prev&&hex64(e.hash),'CHAINE_INVALIDE',seq);
   const {hash:oldHash,...envelope}=e;
   required(hash(stable(envelope))===oldHash,'EMPREINTE_INVALIDE',seq);
   required(TYPES.has(e.type)&&e.data&&typeof e.data==='object'&&!Array.isArray(e.data),'TYPE_INVALIDE',seq);
   required(present(e.context)&&normalize(e.context)!=='*','CONTEXTE_INVALIDE',seq);
   const date=Date.parse(e.at);
   required(Number.isFinite(date)&&date>=priorAt,'HORODATAGE_INVALIDE',seq);priorAt=date;
   if(context===null)context=e.context;
   const d=e.data;
   if(e.type==='CONTEXT'){
    required(d.prior===context&&d.context===e.context&&d.context!==context,'DEPLACEMENT_CONTEXTE_INVALIDE',seq);
    context=e.context;
   }else{
    required(e.context===context,'INDEX_PERIME',seq);
    if(e.type==='SOURCE'){
     required(present(d.id)&&!sources.has(d.id)&&present(d.name)&&present(d.sourceRef)&&present(d.falsifier)&&d.context===context&&hex64(d.sha256)&&Number.isSafeInteger(d.bytes)&&d.bytes>=0&&d.reading==='OCTETS_HACHÉS'&&d.proof==='LOCAL_BYTES_ONLY','SOURCE_NON_ETAYEE',seq);
     const k=Date.parse(d.kRecord),t=d.tEvent?Date.parse(d.tEvent):null;
     required(Number.isFinite(k)&&k<=date+2000&&(t===null||(Number.isFinite(t)&&t<=k+1000)),'TEMPORALITE_T_K',seq);
     sources.set(d.id,d);
    }else if(e.type==='QUESTION'){
     required(present(d.id)&&!questions.has(d.id)&&sources.get(d.sourceId)?.context===context&&present(d.recipient)&&!SELF.has(normalize(d.recipient))&&present(d.cost)&&d.cost.trim().length>=12&&present(d.gap)&&d.gap.trim().length>=12&&d.context===context&&d.status==='GAP_MARKED','QUESTION_NON_SITUEE',seq);
     questions.set(d.id,d);
    }else if(e.type==='ANSWER'){
     const q=questions.get(d.questionId);
     required(q?.context===context&&!answered.has(d.questionId)&&normalize(d.respondent)===normalize(q.recipient)&&!SELF.has(normalize(d.respondent))&&present(d.provenance)&&!SELF.has(normalize(d.provenance))&&present(d.falsifier)&&present(d.content)&&d.priorState==='GAP_MARKED'&&d.state==='ANSWER_CLAIMED'&&d.status==='NON_AUTHENTIFIÉ','REPONSE_INVALIDE',seq);
     answered.add(d.questionId);
    }else if(e.type==='CLAIM'){
     const source=sources.get(d.sourceId);
     required(source?.context===context&&present(d.id)&&!claims.has(d.id)&&present(d.statement)&&d.statement.trim().length>8&&present(d.falsifier)&&present(d.subject)&&present(d.proposer)&&d.context===context&&d.epistemic==='E0'&&d.authorization==='NOT_ASSESSED'&&d.execution==='NOT_PERFORMED','ASSERTION_AUTORITE',seq);
     const h=hash(stable({sourceId:d.sourceId,sourceHash:source.sha256,statement:d.statement,falsifier:d.falsifier,subject:d.subject,proposer:d.proposer,context:d.context}));
     required(h===d.statementHash,'ASSERTION_EMPREINTE',seq);claims.set(d.id,d);
    }else if(e.type==='VERIFIER'){
     required(present(d.id)&&!SELF.has(normalize(d.id))&&!verifiers.has(d.id)&&d.context===context&&d.scope==='CLÉ_PINNÉE_LOCALEMENT_IDENTITÉ_NON_PROUVÉE'&&base64(d.keyB64).length===32,'VERIFICATEUR_INVALIDE',seq);
     verifiers.set(d.id,d);
    }else if(e.type==='REVIEW'){
     const cl=claims.get(d.claimId),v=verifiers.get(d.verifierId);
     required(cl&&v&&!reviewed.has(d.claimId)&&cl.context===context&&v.context===context&&!SELF.has(normalize(d.verifierId))&&normalize(d.verifierId)!==normalize(cl.subject)&&normalize(d.verifierId)!==normalize(cl.proposer),'AUTO_EVALUATION_OU_REVUE_INCONNUE',seq);
     const source=sources.get(cl.sourceId);
     required(d.context===context&&d.sourceHash===source.sha256&&d.statementHash===cl.statementHash&&['SATISFIED','VIOLATED'].includes(d.decision)&&d.status==='SIGNATURE_VALIDE_CLÉ_LOCALE_IDENTITÉ_NON_VÉRIFIÉE','REVUE_LIAISON_INVALIDE',seq);
     const key=base64(v.keyB64),signature=base64(d.signatureB64);
     required(key.length===32&&signature.length===64,'SIGNATURE_TAILLE',seq);
     const der=Buffer.concat([Buffer.from('302a300506032b6570032100','hex'),key]);
     const pub=createPublicKey({key:der,format:'der',type:'spki'});
     const message=stable({schema:'VIGIE-ATTEST-V1',claimId:cl.id,context:cl.context,statementHash:cl.statementHash,sourceHash:source.sha256,decision:d.decision,verifierId:d.verifierId});
     required(verifyEd25519(null,Buffer.from(message),pub,signature),'SIGNATURE_INVALIDE',seq);
     reviewed.add(d.claimId);signatures++;
    }else if(e.type==='REFUSAL')required(present(d.reason),'REFUS_NON_DOCUMENTE',seq);
   }
   prev=e.hash;
  }
  if(receipt){
   required(hex64(receipt.tip)&&Number.isSafeInteger(receipt.count)&&present(receipt.context),'RECU_INVALIDE');
   required(receipt.tip===prev&&receipt.count===doc.events.length&&receipt.context===(context??'session-01'),'RECU_NON_CONCORDANT');
  }
  return {ok:true,code:receipt?'RECU_CONCORDANT_NON_AUTHENTIFIANT':'CHAINE_SITUEE_NON_AUTHENTIFIANTE',count:doc.events.length,tip:prev,context:context??'session-01',signatures_valides_cle_locale:signatures,identity:'NON_VERIFIEE',modelAuthority:'none',authorization:'NOT_ASSESSED',canon:'NON_ADOPTE'};
 }catch(e){return {ok:false,code:e.code||'VERIFICATION_IMPOSSIBLE',seq:e.seq??null,message:String(e.message)};}
}
if(process.argv[1]&&import.meta.url===new URL('file://'+process.argv[1]).href){
 if(process.argv.length<3||process.argv.length>4){console.error('Usage: node verify.mjs export.json [recu.json]');process.exit(2);}
 try{const d=JSON.parse(readFileSync(process.argv[2],'utf8')),r=process.argv[3]?JSON.parse(readFileSync(process.argv[3],'utf8')):null;const outcome=inspect(d,r);console.log(JSON.stringify(outcome,null,2));if(!outcome.ok)process.exitCode=1;}catch(e){console.error(String(e));process.exitCode=2;}
}