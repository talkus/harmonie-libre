/**
 * Vigie Indexicale — remote static-asset probe (v0.7)
 * This checks bytes reached over HTTPS, not deployment identity, civil identity,
 * browser functionality or authorization. No file uploads, no authentication.
 */
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const S = v => typeof v === 'string' && v.trim().length>0;
const h = buf => createHash('sha256').update(buf).digest('hex');
const ASSETS=Object.freeze(['index.html','core.mjs','anchor-core.mjs','ancrage.html','ancrage.mjs','app.js','styles.css']);
const h64=x=> typeof x==='string' && /^[a-f0-9]{64}$/.test(x);
const hostOK=hostname=>hostname==='vigie-indexicale-tikkun.netlify.app'||(/^[a-z0-9-]+--vigie-indexicale-tikkun\.netlify\.app$/.test(hostname));
const fail=(code,detail)=>({ok:false,code,detail:detail||null});

/**
 * @param {object} cfg {siteUrl, expectedAssets: {file: sha256}, fetchImpl, timeoutMs}
 * @returns {object} remote observed asset bytes and security headers, not a browser test
 */
export async function probeNetlify(cfg={}){
  const {siteUrl, expectedAssets, fetchImpl=fetch, timeoutMs=10000}=cfg;
  let base;
  try {base=new URL(siteUrl);} catch {return fail('URL_INVALIDE');}
  if(base.protocol!=='https:'||!hostOK(base.hostname)||base.username||base.password||base.port||base.search||base.hash||base.pathname!=='/')return fail('URL_HORS_SITE_PROTEGE');
  if(!expectedAssets||typeof expectedAssets!=='object'||Array.isArray(expectedAssets)||Object.keys(expectedAssets).length!==ASSETS.length || ASSETS.some(f=>!h64(expectedAssets[f]))){return fail('MANIFESTE_INVALIDE');}
  if(typeof fetchImpl!=='function'||!Number.isFinite(timeoutMs)||timeoutMs<100||timeoutMs>30000)return fail('CONFIG_INVALIDE');
  const measurements=[];
  for(const filename of ASSETS){
    const url=new URL(filename,base);
    let resp,buf;
    try {
      // Redirects are never followed. A login wall is a blocker, not an implicit PASS.
      resp=await fetchImpl(url,{redirect:'manual',signal:AbortSignal.timeout(timeoutMs),headers:{'accept':'*/*','cache-control':'no-cache'}});
      if(!resp || resp.status!==200) return { ...fail('HTTP_INDISPONIBLE', {filename,status:resp?.status??null}),measurements};
      if(resp.redirected||resp.url && new URL(resp.url).origin!==base.origin) return {...fail('REDIRECTION_DE_SOURCE', {filename}),measurements};
      buf=Buffer.from(await resp.arrayBuffer());
    } catch(e){return {...fail('REQUETE_IMPOSSIBLE',{filename,error:e?.name||'UNKNOWN'}),measurements};}
    const measured=h(buf);
    measurements.push({filename,sha256:measured,bytes:buf.length,contentType:resp.headers?.get('content-type')||null});
    if(measured!==expectedAssets[filename])return {...fail('OCTETS_DISTANTS_DIFFERENTS',{filename,expected:expectedAssets[filename],actual:measured}),measurements};
    const type=resp.headers?.get('content-type')||'';
    if(filename.endsWith('.mjs')||filename.endsWith('.js')){
      if(!/^(text|application)\/javascript\b/i.test(type))return {...fail('TYPE_JAVASCRIPT_NON_CONFORME',{filename,contentType:type}),measurements};
    } else if(filename.endsWith('.html') && !/^text\/html\b/i.test(type))return {...fail('TYPE_HTML_NON_CONFORME',{filename,contentType:type}),measurements};
    if((resp.headers?.get('x-content-type-options')||'').toLowerCase()!=='nosniff')return {...fail('NOSNIFF_ABSENT',{filename}),measurements};
    if(filename==='index.html' && !S(resp.headers?.get('content-security-policy')))return {...fail('CSP_ABSENTE',{filename}),measurements};
  }
  return {ok:true,code:'OCTETS_DISTANTS_CONCORDANTS_NON_AUTHENTIFIANTS',siteUrl:base.origin,measurements,netlifyDeployId:'NON_ETABLI',browserExecution:'NON_TESTEE',sourceAuthenticity:'NON_ETABLIE',authorization:'NOT_ASSESSED',modelAuthority:'none',epistemic:'E0'};
}

export function manifestFromDirectory(dir){
  const result={};
  for(const filename of ASSETS)result[filename]=h(readFileSync(resolve(dir,filename)));
  return result;
}

if(process.argv[1] && import.meta.url===new URL('file://'+process.argv[1]).href){
  if(process.argv.length!==5){console.error('Usage: node netlify-remote-probe.mjs https://vigie-indexicale-tikkun.netlify.app/ public-dir expected-manifest.json');process.exit(2)}
  const [url,dir,manifestPath]=process.argv.slice(2);
  try{
    const expected=JSON.parse(readFileSync(manifestPath,'utf8'));
    const local=manifestFromDirectory(dir);
    if(ASSETS.some(f=>local[f]!==expected[f])){
      console.log(JSON.stringify(fail('EMPREINTES_LOCALES_NON_CONFORMES'),null,2));process.exit(1)
    }
    const outcome=await probeNetlify({siteUrl:url,expectedAssets:expected});console.log(JSON.stringify(outcome,null,2));process.exitCode=outcome.ok?0:1;
  }catch(e){console.error(JSON.stringify(fail('MANIFESTE_OU_FICHIERS_ILLISIBLES',e.message)));process.exitCode=2;}
}
