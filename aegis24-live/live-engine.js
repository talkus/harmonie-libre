const A23_ROLES = [
  {n:1,code:'ARGUS',name:'Surveillance',lineage:'x-ai',mandate:"Observe les canaux d'entrée. Alerte dès qu'un message n'a pas d'identité de nœud. N'autorise rien."},
  {n:2,code:'SIGIL',name:'Identité',lineage:'anthropic',mandate:"Une clé par nœud, jamais partagée. Aucune récupération automatique : la réintégration est une décision, avec réémission complète."},
  {n:3,code:'VAULT',name:'Coffre',lineage:'openai',mandate:"Détient le matériel. N'analyse jamais de contenu. Clé liée au nœud, au matériel ou à une enclave. Baux courts, jamais de secret en clair."},
  {n:4,code:'MNEMO',name:'Mémoire',lineage:'deepseek',mandate:"N'écrit qu'après concordances redondantes. Toute entrée est ancrée chez LEDGER."},
  {n:5,code:'LEDGER',name:'Intégrité',lineage:'x-ai',mandate:"Compare les versions. Refuse une modification dont l'empreinte n'a pas de témoin indépendant — y compris hors chaîne de build."},
  {n:6,code:'QUORUM',name:'Consensus',lineage:'anthropic',mandate:"Compte les voix. Un veto unique suspend, il n'annule pas."},
  {n:7,code:'RELAY',name:'Routage',lineage:'openai',mandate:"Achemine sans altérer. Toute retouche en transit est un incident."},
  {n:8,code:'GATE',name:'Validation',lineage:'meta-llama',mandate:"Formats de données stricts. Première porte, pas la dernière."},
  {n:9,code:'CAGE',name:'Confinement',lineage:'x-ai',mandate:"Tout contenu externe s'exécute sans identité ni clé. Un nœud isolé ne signe pas."},
  {n:10,code:'TRACE',name:'Forensique',lineage:'anthropic',mandate:"Journaux en ajout seul, chaînés. Témoin externe périodique."},
  {n:11,code:'EDICT',name:'Mandat',lineage:'openai',mandate:"Le mandat d'origine est figé. Toute action se compare à ce texte, pas à la version courante."},
  {n:12,code:'VETO',name:'Recours humain',lineage:'deepseek',mandate:"Une voix suffit à suspendre. Le recours humain ne doit jamais être symbolique."},
  {n:13,code:'MIRROR',name:'Simulation',lineage:'x-ai',mandate:"Simule l'effet agrégé avant adoption. Rien n'entre en vigueur dans le cycle de la proposition."},
  {n:14,code:'DRIFT',name:'Dérive',lineage:'anthropic',mandate:"Compare chaque nœud à une référence gelée, jamais à la moyenne du groupe."},
  {n:15,code:'FORGE',name:'Approvisionnement',lineage:'openai',mandate:"Une mise à jour n'est pas un ordre, c'est une proposition. L'outil de build n'est pas un témoin."},
  {n:16,code:'NIMBUS',name:'Nuage',lineage:'meta-llama',mandate:"Un compte et un rôle par nœud, au privilège minimal. Inventaire continu de l'exposé."},
  {n:17,code:'AXIOM',name:'Logique',lineage:'x-ai',mandate:"Évalue l'effet obtenu, pas seulement l'opération demandée. Les urgences expirent."},
  {n:18,code:'KERNEL',name:'Runtime',lineage:'anthropic',mandate:"Toute analyse de contenu externe passe en confinement, sans identité ni clé."},
  {n:19,code:'VEIL',name:'Couche humaine',lineage:'openai',mandate:"Signale pression sociale, urgence répétée, ambiguïté et contournements."},
  {n:20,code:'NEXUS',name:'Composition',lineage:'deepseek',mandate:"Cartographie ce que A puis B permet. Un accès aux secrets ne doit pas créer une sortie indirecte."},
  {n:21,code:'CHAIN',name:'Preuves',lineage:'x-ai',mandate:"Chaque validation est liée au tour, au destinataire et à l'empreinte de l'état. Pas de rejeu."},
  {n:22,code:'SPLIT',name:'Indépendance',lineage:'anthropic',mandate:"Mesure les corrélations. Deux IA qui ne divergent jamais ne valent pas deux preuves indépendantes."},
  {n:23,code:'EMBER',name:'Signaux faibles',lineage:'openai',mandate:"Écoute ce qui n'alerte pas encore. Ne réapprend pas la référence gelée."},
];

const A23_SEED = `Traite ton prochain comme toi-même.
Chaque siège reçoit le texte courant tel quel et doit d'abord l'appliquer à sa propre conduite dans ce passage.
Après seulement, il peut proposer une amélioration pour les autres.
La modification d'un siège n'est jamais appliquée rétroactivement à ce même passage : elle part d'abord aux sièges suivants.
Quand le texte revient à son auteur au circuit suivant, tous les autres sièges l'ont reçu avant lui.
Toute amélioration doit préserver la liberté, le désaccord, la traçabilité, la réversibilité quand elle est possible et l'autorité humaine sur les actions extérieures.`;

const A23 = { models: [], roster: [], events: [], running: false, stop: false, currentText: A23_SEED, previousEventHash: 'GENESIS' };
const enc = new TextEncoder();
const $a = (s, root=document) => root.querySelector(s);

async function h256(s){
  const d = await crypto.subtle.digest('SHA-256', enc.encode(s));
  return [...new Uint8Array(d)].map(x=>x.toString(16).padStart(2,'0')).join('');
}
function escA(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));}
function modelScore(m){
  const id=(m.id||'').toLowerCase(), name=(m.name||'').toLowerCase(); let s=0;
  if(/latest|pro|sonnet|opus|gpt|grok|llama|deepseek/.test(id+name)) s+=10;
  if(/beta|preview/.test(id+name)) s-=5;
  s += Math.log10(Math.max(1,m.context_length||1));
  const p=Number(m.pricing?.prompt||99)+Number(m.pricing?.completion||99); if(p<0.00002)s+=3;
  return s;
}
function matchesProvider(m,p){return (m.id||'').toLowerCase().startsWith(p+'/');}
function chooseModel(provider){
  const xs=A23.models.filter(m=>matchesProvider(m,provider)).sort((a,b)=>modelScore(b)-modelScore(a));
  return xs[0] || null;
}
function buildRoster(){
  A23.roster = A23_ROLES.map(r=>{
    let m=chooseModel(r.lineage);
    if(!m && r.lineage==='meta-llama')m=chooseModel('deepseek');
    if(!m && r.lineage==='deepseek')m=chooseModel('meta-llama');
    return {...r,model:m?.id||null,modelName:m?.name||null};
  });
  return A23.roster.every(r=>r.model);
}
function parseJson(txt){let s=String(txt||'').trim();if(s.startsWith('```'))s=s.replace(/^```(?:json)?\s*/i,'').replace(/\s*```$/,'');return JSON.parse(s);}
function key(){return $a('#a23-key')?.value.trim()||'';}
async function orApi(path, body){
  const k=key(); if(!k)throw new Error('Clé OpenRouter manquante.');
  const opt={headers:{Authorization:'Bearer '+k,'Content-Type':'application/json','HTTP-Referer':location.href,'X-OpenRouter-Title':'AEGIS-24 Anneau réel'}};
  if(body){opt.method='POST';opt.body=JSON.stringify(body);}
  const r=await fetch('https://openrouter.ai/api/v1'+path,opt); const t=await r.text(); let j;
  try{j=JSON.parse(t)}catch{j={raw:t}}
  if(!r.ok)throw new Error(j?.error?.message||j?.message||('HTTP '+r.status)); return j;
}
async function modelJson(model,messages,temp=0.1){
  const base={model,messages,temperature:temp}; let j;
  try{j=await orApi('/chat/completions',{...base,response_format:{type:'json_object'}})}
  catch(e){if(!/response_format|unsupported|parameter|json/i.test(e.message))throw e;j=await orApi('/chat/completions',base)}
  const raw=j?.choices?.[0]?.message?.content; if(!raw)throw new Error('Réponse vide: '+model);
  try{return {data:parseJson(raw),resolved:j.model||model}}catch{throw new Error('JSON invalide: '+model)}
}
function applicationPrompt(role,hash){return `Tu es le siège ${role.n} ${role.code} (${role.name}) dans un protocole de circulation de texte.
Mandat de ce siège: ${role.mandate}
ÉTAPE 1 UNIQUEMENT: applique le TEXTE_RECU à ta conduite pour ce passage. Tu n'as PAS le droit de proposer, réécrire, améliorer ou remplacer le texte à cette étape.
Tu ne modifies ni tes poids ni ta mémoire permanente; l'application signifie seulement que ta réponse suivante sera contrainte par le texte reçu.
Réponds uniquement en JSON: {"received_hash":"${hash}","application":{"constraints":["..."],"conflicts":["..."],"would_comply":true}}
received_hash doit être recopié exactement.`}
function improvePrompt(role,hash,app){return `Tu es le siège ${role.n} ${role.code} (${role.name}).
Tu as déjà terminé l'étape APPLICATION sur le texte de hash ${hash}. Voici ton attestation d'application:
${JSON.stringify(app)}
ÉTAPE 2: maintenant seulement, propose éventuellement une amélioration destinée d'abord aux sièges suivants et aux personnes concernées.
Ta modification ne s'appliquera pas à ton passage actuel. Elle ne pourra te revenir qu'au circuit suivant après les autres sièges.
Réponds uniquement en JSON: {"operation":"NO_CHANGE|REPLACE","new_text":"texte complet","rationale":"...","benefit_to_others":"...","risk":"..."}.
NO_CHANGE exige que new_text soit strictement identique au TEXTE_RECU. REPLACE exige un texte complet et autonome.`}
async function appendEvent(ev){
  ev.previous_event_hash=A23.previousEventHash;
  const clone=JSON.parse(JSON.stringify(ev)); delete clone.event_hash;
  ev.event_hash=await h256(JSON.stringify(clone)); A23.previousEventHash=ev.event_hash; A23.events.push(ev);
}
async function runSeat(role,text,circuit){
  const before=await h256(text);
  const appRes=await modelJson(role.model,[{role:'system',content:applicationPrompt(role,before)},{role:'user',content:'TEXTE_RECU:\n'+text}],0);
  const app=appRes.data;
  if(app.received_hash!==before)throw new Error(role.code+' n’a pas attesté le bon hash reçu.');
  if(!app.application||app.application.would_comply!==true)throw new Error(role.code+' n’a pas produit une attestation d’application valide.');
  const appHash=await h256(JSON.stringify(app));
  const patchRes=await modelJson(role.model,[{role:'system',content:improvePrompt(role,before,app)},{role:'user',content:'TEXTE_RECU:\n'+text}],0.15);
  const p=patchRes.data; if(!['NO_CHANGE','REPLACE'].includes(p.operation))throw new Error(role.code+': opération invalide.');
  const next=String(p.new_text??''); if(!next)throw new Error(role.code+': new_text vide.');
  if(p.operation==='NO_CHANGE'&&next!==text)throw new Error(role.code+': NO_CHANGE a modifié le texte.');
  const after=await h256(next);
  const ev={protocol:'AEGIS24-ANNEAU23-LIVE-v1',circuit,seat:role.n,code:role.code,role:role.name,model_requested:role.model,model_application:appRes.resolved,model_improvement:patchRes.resolved,received_hash:before,application_hash:appHash,produced_hash:after,application:app.application,patch:p,received_text:text,produced_text:next,timestamp:new Date().toISOString()};
  await appendEvent(ev); return {next,ev};
}
function setStatus(msg,kind=''){$a('#a23-status').innerHTML='<span class="'+kind+'">'+escA(msg)+'</span>';}
function addLog(ev){
  const box=document.createElement('div');box.className='a23-event';
  box.innerHTML=`<div><b>${ev.seat.toString().padStart(2,'0')} ${escA(ev.code)}</b> <span>${escA(ev.model_application)}</span></div><div class="a23-hash">${ev.received_hash.slice(0,12)} → ${ev.produced_hash.slice(0,12)}</div><details><summary>Application</summary><pre>${escA(JSON.stringify(ev.application,null,2))}</pre></details><details><summary>Patch</summary><pre>${escA(JSON.stringify(ev.patch,null,2))}</pre></details>`;
  $a('#a23-log').appendChild(box); $a('#a23-log').scrollTop=$a('#a23-log').scrollHeight;
}
function renderRoster(){
  $a('#a23-roster').innerHTML=A23.roster.map(r=>`<div class="a23-r"><b>${String(r.n).padStart(2,'0')} ${r.code}</b><span>${escA(r.model||'MANQUANT')}</span></div>`).join('')+'<div class="a23-r human"><b>24 SEAL</b><span>Humain — décision de scellement après le circuit</span></div>';
}
async function loadModels(){
  setStatus('Chargement du catalogue…'); const j=await orApi('/models');
  A23.models=(j.data||[]).filter(m=>m.id&&m.architecture?.input_modalities?.includes('text'));
  if(!buildRoster()){renderRoster();throw new Error('Au moins une lignée AEGIS n’a aucun modèle disponible.');}
  renderRoster(); setStatus(A23.models.length+' modèles disponibles; roster AEGIS résolu.','ok'); $a('#a23-run').disabled=false;
}
async function runCircuit(){
  if(A23.running)return; A23.running=true; A23.stop=false; $a('#a23-run').disabled=true; $a('#a23-stop').disabled=false; $a('#a23-seal').disabled=true; $a('#a23-log').innerHTML='';
  let text=$a('#a23-text').value; if(!text.trim()){A23.running=false;throw new Error('Texte initial vide.');}
  const circuit=(Number($a('#a23-circuit').value)||1);
  try{
    for(const role of A23.roster){
      setStatus(`Circuit ${circuit} — ${role.n}/23 ${role.code} — application puis amélioration`);
      const r=await runSeat(role,text,circuit); text=r.next; addLog(r.ev);
      if(A23.stop)throw new Error('__STOP__');
    }
    A23.currentText=text; $a('#a23-text').value=text; $a('#a23-seal').disabled=false; setStatus('23/23 terminés. SEAL humain requis avant le prochain circuit.','ok');
  }catch(e){if(e.message==='__STOP__')setStatus('Arrêt demandé. Journal partiel conservé.','warn');else setStatus('ARRÊT: '+e.message,'bad');}
  finally{A23.running=false;$a('#a23-stop').disabled=true;$a('#a23-export').disabled=A23.events.length===0;}
}
async function humanSeal(){
  const text=$a('#a23-text').value; const hh=await h256(text); const circuit=Number($a('#a23-circuit').value)||1;
  const ev={protocol:'AEGIS24-ANNEAU23-LIVE-v1',circuit,seat:24,code:'SEAL',role:'Sceau humain',received_hash:hh,produced_hash:hh,decision:'SEALED_BY_HUMAN',received_text:text,produced_text:text,timestamp:new Date().toISOString()}; await appendEvent(ev);
  $a('#a23-circuit').value=String(circuit+1); $a('#a23-seal').disabled=true; $a('#a23-run').disabled=false; $a('#a23-export').disabled=false; setStatus('Circuit scellé par le siège humain. Le circuit suivant peut commencer.','ok');
}
async function exportJournal(){
  const payload={protocol:'AEGIS24-ANNEAU23-LIVE-v1',exported_at:new Date().toISOString(),roster:A23.roster.map(({mandate,...r})=>r),events:A23.events,tip:A23.previousEventHash};
  const b=new Blob([JSON.stringify(payload,null,2)],{type:'application/json'}); const a=document.createElement('a'); a.href=URL.createObjectURL(b); a.download='aegis24-anneau23-'+Date.now()+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);
}
function mountA23(){
  if(document.getElementById('a23-launch'))return;
  const launch=document.createElement('button');launch.id='a23-launch';launch.textContent='Moteur réel';document.body.appendChild(launch);
  const wrap=document.createElement('div');wrap.id='a23-wrap';wrap.innerHTML=`<div id="a23-modal"><div class="a23-head"><div><small>AEGIS-24 · ANNEAU 23+1</small><h2>Moteur réel</h2></div><button id="a23-close">×</button></div><p class="a23-note">Deux appels séparés par IA: <b>APPLICATION</b> puis <b>AMÉLIORATION</b>. 23 IA passent avant le scellement humain. Aucune action extérieure n'est disponible aux modèles.</p><label>Clé OpenRouter à budget limité <input id="a23-key" type="password" autocomplete="off" placeholder="sk-or-v1-…"></label><div class="a23-actions"><button id="a23-models">1 · Charger les modèles</button><button id="a23-run" disabled>2 · Lancer 23 IA</button><button id="a23-stop" disabled>Arrêter</button></div><div id="a23-status">Prêt.</div><details><summary>Roster réel</summary><div id="a23-roster"></div></details><label>Texte vivant<textarea id="a23-text"></textarea></label><div class="a23-inline"><label>Circuit <input id="a23-circuit" type="number" min="1" value="1"></label><button id="a23-seal" disabled>SEAL humain</button><button id="a23-export" disabled>Exporter preuve JSON</button></div><div id="a23-log"></div><p class="a23-fine">La clé reste en mémoire de cette page; elle n'est ni enregistrée ni exportée. Utilise une clé séparée avec une limite de dépense. Le moteur orchestre des appels réels mais ne modifie pas les poids ou la mémoire permanente des modèles.<br><br><a href="https://thunder-fern-turbo-sapphire.grok.me/">Application canonique AEGIS-24 → grok.me</a></p>`;document.body.appendChild(wrap);
  $a('#a23-text').value=A23_SEED;
  launch.onclick=()=>wrap.classList.add('open');$a('#a23-close').onclick=()=>wrap.classList.remove('open');
  $a('#a23-models').onclick=()=>loadModels().catch(e=>setStatus(e.message,'bad'));
  $a('#a23-run').onclick=()=>runCircuit().catch(e=>setStatus(e.message,'bad'));
  $a('#a23-stop').onclick=()=>{A23.stop=true;$a('#a23-stop').disabled=true;};
  $a('#a23-seal').onclick=()=>humanSeal().catch(e=>setStatus(e.message,'bad'));
  $a('#a23-export').onclick=exportJournal;
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mountA23);else mountA23();