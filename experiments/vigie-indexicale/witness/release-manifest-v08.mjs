/* Vigie v0.8: lecture contradictoire d'un reçu de release.
 * Implémentation séparée du code navigateur et du client HTTP.
 * Aucun secret, aucun accès réseau, aucun droit d'adoption.
 */
import {createHash} from 'node:crypto';
const H=x=>createHash('sha256').update(x).digest('hex');
const h64=x=>typeof x==='string'&&/^[a-f0-9]{64}$/.test(x);
const git=x=>typeof x==='string'&&/^[a-f0-9]{40}$/.test(x);
const files=['index.html','core.mjs','anchor-core.mjs','ancrage.html','ancrage.mjs','app.js','styles.css'];
const shape=(o,keys)=>o&&typeof o==='object'&&!Array.isArray(o)&&Object.keys(o).length===keys.length&&keys.every(k=>Object.hasOwn(o,k));
const refuse=(code)=>({ok:false,code,authorization:'NOT_ASSESSED',epistemic:'E0'});
export function verifyHostedRelease(receiptBytes,pin,assetBytes){
  try{
    if(!Buffer.isBuffer(receiptBytes)||!shape(pin,['schema','siteId','gitHead','gitPr','staticArchiveSha256','assets','releaseSha256','source','authorization'])||pin.schema!=='VIGIE-RELEASE-PIN-V1'||!pin.siteId||!git(pin.gitHead)||pin.gitPr!==31||!h64(pin.staticArchiveSha256)||!h64(pin.releaseSha256)||!shape(pin.assets,files)||!files.every(x=>h64(pin.assets[x]))||pin.source!=='OUT_OF_BAND_REQUIRED'||pin.authorization!=='NOT_ASSESSED')return refuse('PIN_INVALIDE');
    if(receiptBytes.length>16384||H(receiptBytes)!==pin.releaseSha256)return refuse('RECU_HORS_PIN');
    const r=JSON.parse(receiptBytes.toString('utf8'));
    if(!shape(r,['schema','siteId','gitHead','gitPr','staticArchiveSha256','assets','modelAuthority','authorization','provenance'])||r.schema!=='VIGIE-RELEASE-V1'||r.siteId!==pin.siteId||r.gitHead!==pin.gitHead||r.gitPr!==pin.gitPr||r.staticArchiveSha256!==pin.staticArchiveSha256||r.modelAuthority!=='none'||r.authorization!=='NOT_ASSESSED'||r.provenance!=='PINS_DECLARES_NON_AUTHENTIFIES'||!shape(r.assets,files)||files.some(x=>r.assets[x]!==pin.assets[x]))return refuse('RECU_CHAINE_INCOHERENTE');
    if(!shape(assetBytes,files)||files.some(x=>!Buffer.isBuffer(assetBytes[x])))return refuse('ACTIFS_NON_FOURNIS');
    const observed=[];
    for(const f of files){const b=assetBytes[f];if(b.length>2097152||H(b)!==r.assets[f])return refuse('ACTIF_HORS_PIN');observed.push({file:f,sha256:H(b),bytes:b.length});}
    return {ok:true,code:'CONCORDANCE_OCTETS_NON_AUTHENTIFIANTE',observed,releaseSha256:H(receiptBytes),modelAuthority:'none',authorization:'NOT_ASSESSED',epistemic:'E0',identity:'NON_ETABLIE',deployReady:'NON_ETABLI',browser:'NON_TESTE',canon:'NOT_ADOPTED'};
  }catch{return refuse('RECU_ILLISIBLE_OU_INCOMPLET');}
}