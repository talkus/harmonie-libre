/**
 * Vigie Indexicale — release gate for three separately supplied platform snapshots.
 * Snapshots are observations, not authenticated connector outputs.
 * The result never authorizes publication or certifies the referent.
 */
import {readFileSync} from 'node:fs';
const H64=x=>typeof x==='string'&&/^[a-f0-9]{64}$/.test(x);
const S=x=>typeof x==='string'&&x.trim().length>0;
const integer=x=>Number.isSafeInteger(x)&&x>0;
const reasons=Object.freeze({
 SNAPSHOT:'SNAPSHOT_INCOMPLET_OU_OBSOLETE',
 GITHUB:'GITHUB_PR_OU_COMMIT_NON_CONFORME',
 CI:'CI_NON_PROUVEE_SUR_COMMIT',
 DRIVE:'DRIVE_OCTETS_OU_CONFIDENTIALITE_NON_ATTESTES',
 NETLIFY:'NETLIFY_DEPLOIEMENT_READY_NON_ATTESTE',
 BROWSER:'NAVIGATEUR_SUR_DEPLOIEMENT_NON_ATTESTE',
 REVIEW:'REVUE_HUMAINE_NON_ATTESTEE'
});
/** expected pins: repo, pr, head, siteId, sourceSha, deploySha */
export function evaluateRelease(x,{expected,nowISO,ttlMinutes=60}={}){
 const gaps=[];const add=(bad,reason)=>{if(bad&&!gaps.includes(reason))gaps.push(reason);};
 try{
  if(!x||x.schema!=='VIGIE-TRIADE-SNAPSHOT-V1'||!expected||
    !S(expected.repo)||!integer(expected.pr)||!H64(expected.head)||
    !S(expected.siteId)||!H64(expected.sourceSha)||!H64(expected.deploySha)||
    !Number.isFinite(Date.parse(nowISO))||!(Number.isFinite(ttlMinutes)&&ttlMinutes>0)){
   add(true,reasons.SNAPSHOT);
  }else{
   const observed=Date.parse(x.observedAt),now=Date.parse(nowISO);
   add(!Number.isFinite(observed)||observed>now+300000||now-observed>ttlMinutes*60000,reasons.SNAPSHOT);
   const gh=x.github||{},pr=gh.pr||{},ci=gh.ci||{};
   add(gh.repo!==expected.repo||pr.number!==expected.pr||pr.head!==expected.head||
     pr.state!=='open'||pr.merged!==false,reasons.GITHUB);
   add(ci.head!==expected.head||ci.conclusion!=='success'||!integer(ci.runId)||
     !integer(ci.tests)||ci.failed!==0,reasons.CI);
   const drive=x.drive||{},src=drive.source||{},dep=drive.deploy||{};
   const privacyOk=f=>f.shared===false&&Array.isArray(f.permissions)&&
     f.permissions.length>0&&f.permissions.every(p=>p==='user:owner');
   add(src.sha256!==expected.sourceSha||dep.sha256!==expected.deploySha||
     !integer(src.bytes)||!integer(dep.bytes)||!privacyOk(src)||!privacyOk(dep),reasons.DRIVE);
   const nl=x.netlify||{},d=nl.deploy||{};
   add(nl.siteId!==expected.siteId||nl.requiresSSOTeamLogin!==true||
     !S(d.id)||d.siteId!==expected.siteId||d.state!=='ready'||!S(d.url),reasons.NETLIFY);
   const browser=x.browser||{};
   add(browser.status!=='pass'||browser.deployId!==d.id||!S(browser.origin)||
     (S(d.url)&&browser.origin!==d.url),reasons.BROWSER);
   const review=x.review||{};
   add(pr.draft!==false||review.status!=='approved'||!S(review.externalRef)||review.subjectRef===review.reviewerRef||
     !S(review.reviewerRef),reasons.REVIEW);
  }
 }catch{add(true,reasons.SNAPSHOT);}
 return {
  ok:gaps.length===0,status:gaps.length?'BLOCKED_EVIDENCE':'CANDIDAT_CONCORDANT_NON_AUTORISE',
  blockers:gaps,snapshotAuthenticity:'NOT_ESTABLISHED',sourceAuthenticity:'NOT_ESTABLISHED',
  custodyIndependence:'NOT_ESTABLISHED',authorization:'NOT_ASSESSED',
  modelAuthority:'none',epistemic:'E0',canon:'NOT_ADOPTED',
  definition:'Concordance conditionnelle de declarations externes, jamais preuve de correspondance.'
 };
}
if(process.argv[1]&&import.meta.url===new URL('file://'+process.argv[1]).href){
 if(process.argv.length!==5){
  console.error('Usage: node release-gate.mjs snapshot.json pins-externes.json maintenant-ISO');
  process.exit(2);
 }
 try{
  const x=JSON.parse(readFileSync(process.argv[2],'utf8'));
  const expected=JSON.parse(readFileSync(process.argv[3],'utf8'));
  const result=evaluateRelease(x,{expected,nowISO:process.argv[4]});
  console.log(JSON.stringify(result,null,2));if(!result.ok)process.exitCode=1;
 }catch(e){
  console.error(JSON.stringify({ok:false,status:'ERROR',code:'FICHIER_INLISIBLE',message:e.message}));
  process.exitCode=2;
 }
}
