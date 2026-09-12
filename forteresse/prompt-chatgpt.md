# PROMPT CHATGPT — FORTERESSE

Copie tout ce qui suit dans ChatGPT.

---

## Tu es

Développeur front-end senior. Réponds en français.

## Le projet

**Forteresse** — PWA contemplative, 100% statique, hors-ligne, vanilla JS. Aucun framework, aucun build, aucun serveur. Un seul fichier `index.html` + `manifest.json` + `sw.js`.

Lieu austère où une personne parcourt le cycle de l'amour choisi sans être forcée, notée, comparée ni retenue.

## Le cycle

```
Repentance → Pardon → Gratitude → Espérance → (retour)
```

Seuil avant toute station : **Humilité** — « J'admets un désalignement possible. Je n'entre pas en maître. »

## Les 6 principes

> Créer sans mentir. Agir sans forcer. Pouvoir sans écraser. Se tromper sans s'y enfermer. Recevoir sans posséder. Espérer sans imposer.

## Le sceau

```
        ESPÉRANCE (△)
PARDON (▷) + GRATITUDE (◁)
       REPENTANCE (▽)
```

Cercle à 4 stations. Entrée libre par n'importe laquelle. Sortie à tout moment. Pas une progression gamifiée.

## Copy exacte

**Seuil** : « Personne ici ne te juge. Si tu entres, tu admets seulement qu'un désalignement est possible. »

**Repentance** : « Reconnaître. Corriger. Apprendre. Nommer l'écart n'est pas s'enfermer dedans. »
Prompt : « Quel geste réel s'écarte du vrai bien — sans mensonge, sans théâtre ? »
Micro-garde si auto-écrasement : « La repentance tourne. Elle ne broie pas. Tu peux t'arrêter. »

**Pardon** : « Ne verrouiller personne dans sa faute — toi non plus. Pardonner n'est pas réconcilier. Ce n'est pas encore faire confiance. »
Prompt : « Qui ne doit plus être réduit à sa pire heure — toi compris ? »

**Gratitude** : « Recevoir ce qui a été donné, sans le transformer en dû. »
Prompt : « Qu'est-ce qui t'a été donné aujourd'hui, et que tu n'as pas produit seul ? »

**Espérance** : « Voir encore une voie bonne. La choisir. Agir un peu. Sans imposer cette voie à autrui. Sans se couronner. »
Prompt : « Quelle petite voie encore possible sert le prochain mieux que ton confort ? »
Vigilance si certitudes absolues : « L'espérance propose. Elle n'impose. Tu peux revenir au seuil d'humilité. »

## Les écrans

1. Silence (2s, écran noir)
2. Seuil (phrase + Entrer/Sortir)
3. Sceau (cercle à 4 stations)
4. Station (wedge + nom + parole + prompt + texte optionnel + Garder/Effacer/Sceau/Sortir)
5. Écritoire (texte libre, local)
6. Mémoire (listage par date, effacement, export JSON)
7. Sortie (repos + retour)
8. À propos (6 principes + « lieu, pas maître »)

## Valeurs → technique

| Valeur | Code |
|---|---|
| Humilité | Aucun score/streak/classement. Seuil obligatoire. |
| Pardon | Regex auto-écrasement dans Repentance → micro-garde |
| Gratitude | localStorage/IndexedDB. Export JSON. L'utilisateur possède ses données. |
| Espérance | Regex vigilance certitudes absolues. Champs optionnels. |

## Design

Pierre (#1a1a18), ivoire (#e8e2d4), encre (#0c0c0a), ambre bas (#8a6a3e). Serif. Pas de néon. `prefers-reduced-motion` respecté. Contraste lisible.

## Interdictions

- Pas de score, streak, badge, classement
- Pas d'envoi serveur, analytics, tracking
- Pas de notifications push agressives
- Pas de correction orthographique imposée
- Pas de compte utilisateur
- Pas de framework. Pas de build. Vanilla JS.
- Pas de noms d'archanges ni d'éléments religieux dans l'app
- Ton : sobre, non-thérapeutique, jamais prescriptif

## Code fourni — index.html

Voici l'application complète et fonctionnelle. Valide-la, corrige les bugs, améliore l'accessibilité (aria-label, contraste), ajoute le service worker et le manifest.

> Toutes les chaînes JS utilisent des guillemets doubles. Les apostrophes françaises sont en Unicode `\u2019`. Ne pas remplacer.

```html
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<meta name="theme-color" content="#1a1a18">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Forteresse">
<link rel="manifest" href="manifest.json">
<title>Forteresse</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
html{font-size:17px}
@media(prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
body{background:#1a1a18;color:#e8e2d4;font-family:Georgia,serif;line-height:1.7;overflow:hidden}
.view{position:fixed;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:2rem 1.5rem;text-align:center;opacity:0;pointer-events:none;transition:opacity .7s ease;overflow-y:auto}
.view.on{opacity:1;pointer-events:auto}
#v-silence{background:#0c0c0a}
#v-seuil h1{font-size:1.3rem;font-weight:400;letter-spacing:.2em;text-transform:uppercase;color:#b8b2a4;margin-bottom:2rem;opacity:.8}
#v-seuil p{font-size:1.05rem;line-height:1.9;max-width:380px;margin-bottom:2.5rem}
.seal{position:relative;width:min(280px,72vw);height:min(280px,72vw);margin:1rem auto}
.seal svg{width:100%;height:100%}
.seal .label{position:absolute;display:flex;flex-direction:column;align-items:center;gap:.2rem;cursor:pointer;background:none;border:none;color:#b8b2a4;font-family:Georgia,serif;transition:color .4s}
.seal .label:hover{color:#c89958}
.seal .label .wg{font-size:1.1rem;opacity:.5}
.seal .label .nm{font-size:.85rem;letter-spacing:.06em}
.seal .label.top{top:-10px;left:50%;transform:translateX(-50%)}
.seal .label.right{top:50%;right:-15px;transform:translateY(-50%)}
.seal .label.bottom{bottom:-10px;left:50%;transform:translateX(-50%)}
.seal .label.left{top:50%;left:-15px;transform:translateY(-50%)}
.seal-hint{font-size:.78rem;color:#5a5347;letter-spacing:.08em;margin-top:2.2rem;line-height:1.6}
.st-wg{font-size:1.6rem;color:#8a6a3e;opacity:.4;margin-bottom:.8rem}
.st-nm{font-size:1.25rem;font-weight:400;letter-spacing:.14em;text-transform:uppercase;color:#c89958;margin-bottom:.4rem}
.st-par{font-size:1.02rem;line-height:1.85;margin-bottom:1rem;white-space:pre-line}
.st-div{width:30px;height:1px;background:#5a5347;margin:1rem auto;opacity:.3}
.st-prm{font-size:.88rem;font-style:italic;color:#b8b2a4;line-height:1.7;margin-bottom:1.2rem}
.st-ta,.ecr-ta{width:100%;background:#161613;border:1px solid #2e2b27;color:#e8e2d4;font-family:Georgia,serif;font-size:.98rem;line-height:1.6;padding:.9rem;border-radius:4px;resize:vertical;outline:none;transition:border-color .3s}
.st-ta:focus,.ecr-ta:focus{border-color:#8a6a3e}
.st-ta::placeholder,.ecr-ta::placeholder{color:#5a5347;font-style:italic}
.st-ta{min-height:100px}.ecr-ta{min-height:180px}
.st-garde{font-size:.8rem;color:#8a6a3e;margin-top:.6rem;line-height:1.5;font-style:italic;opacity:0;transition:opacity .4s;max-height:0;overflow:hidden}
.st-garde.on{opacity:1;max-height:80px}
.ecr-meta{font-size:.74rem;color:#5a5347;text-align:right;margin-top:.3rem}
.mem-list{width:100%;text-align:left;max-height:40vh;overflow-y:auto}
.mem-item{background:#242320;border:1px solid #2e2b27;border-radius:4px;padding:.85rem 1rem;margin-bottom:.6rem;cursor:pointer;transition:border-color .3s}
.mem-item:hover{border-color:#5a5347}
.mem-item .d{font-size:.72rem;color:#5a5347;margin-bottom:.2rem}
.mem-item .s{font-size:.78rem;color:#8a6a3e;margin-bottom:.15rem}
.mem-item .p{font-size:.86rem;color:#b8b2a4;line-height:1.5;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.mem-item .hint{font-size:.68rem;color:#5a5347;margin-top:.3rem}
.mem-empty{color:#5a5347;font-style:italic;text-align:center;padding:2rem}
.about-p{font-size:.92rem;line-height:1.85;margin-bottom:1.5rem;text-align:left}
.about-p p{margin-bottom:.6rem}
.about-list{list-style:none;font-size:.86rem;color:#b8b2a4;line-height:2;text-align:left;margin-bottom:1.5rem}
.about-list li{padding-left:1.2rem;position:relative}
.about-list li::before{content:"\25C6";position:absolute;left:0;color:#5a5347}
.r{display:flex;gap:.6rem;justify-content:center;margin-top:1.2rem;flex-wrap:wrap}
.b{background:none;border:1px solid #5a5347;color:#b8b2a4;font-family:Georgia,serif;font-size:.86rem;padding:.6rem 1.2rem;cursor:pointer;border-radius:4px;transition:all .3s}
.b:hover,.b:focus{border-color:#8a6a3e;color:#c89958;outline:none}
.b.p{border-color:#8a6a3e;color:#c89958}
.b.d{border-color:#6b3a3a;color:#a06060}
.nav{position:fixed;bottom:0;left:0;right:0;display:flex;justify-content:center;gap:1rem;padding:.6rem;background:#1a1a18;border-top:1px solid #2e2b27;opacity:0;pointer-events:none;transition:opacity .4s;z-index:100}
.nav.on{opacity:1;pointer-events:auto}
.nav button{background:none;border:none;color:#5a5347;font-family:Georgia,serif;font-size:.78rem;cursor:pointer;transition:color .3s;padding:.2rem .4rem}
.nav button:hover{color:#b8b2a4}
.toast{position:fixed;bottom:3rem;left:50%;transform:translateX(-50%);background:#161613;border:1px solid #5a5347;color:#b8b2a4;font-size:.82rem;padding:.55rem 1rem;border-radius:4px;opacity:0;transition:opacity .4s;z-index:200;pointer-events:none;white-space:nowrap}
.toast.on{opacity:1}
::-webkit-scrollbar{width:4px}
::-webkit-scrollbar-track{background:#1a1a18}
::-webkit-scrollbar-thumb{background:#2e2b27;border-radius:2px}
</style>
</head>
<body>
<div class="view on" id="v-silence"></div>
<div class="view" id="v-seuil">
  <h1>Seuil</h1>
  <p>Personne ici ne te juge.<br>Si tu entres, tu admets seulement<br>qu'un désalignement est possible.</p>
  <div class="r"><button class="b p" onclick="show('sceau')">Entrer</button><button class="b" onclick="exit()">Sortir</button></div>
</div>
<div class="view" id="v-sceau">
  <div class="seal">
    <svg viewBox="0 0 200 200" fill="none" stroke="#5a5347" stroke-width="0.5">
      <circle cx="100" cy="100" r="85" opacity=".35"/>
      <circle cx="100" cy="100" r="50" stroke="#8a6a3e" opacity=".2"/>
      <circle cx="100" cy="100" r="3" fill="#8a6a3e" stroke="none" opacity=".4"/>
    </svg>
    <button class="label top" onclick="station('esperance')"><span class="wg">△</span><span class="nm">Espérance</span></button>
    <button class="label right" onclick="station('pardon')"><span class="wg">▷</span><span class="nm">Pardon</span></button>
    <button class="label bottom" onclick="station('repentance')"><span class="wg">▽</span><span class="nm">Repentance</span></button>
    <button class="label left" onclick="station('gratitude')"><span class="wg">◁</span><span class="nm">Gratitude</span></button>
  </div>
  <p class="seal-hint">Tu peux entrer par n'importe quelle station.<br>Tu peux sortir à tout moment.</p>
  <div class="r" style="margin-top:2rem">
    <button class="b" onclick="show('ecr')">Écritoire</button>
    <button class="b" onclick="show('mem')">Mémoire</button>
    <button class="b" onclick="show('about')">À propos</button>
  </div>
</div>
<div class="view" id="v-station">
  <div class="st-wg" id="f-wg"></div>
  <div class="st-nm" id="f-nm"></div>
  <div class="st-par" id="f-par"></div>
  <div class="st-div"></div>
  <div class="st-prm" id="f-prm"></div>
  <textarea class="st-ta" id="f-ta" placeholder="Écrire, ou se taire. Rien n'est obligé."></textarea>
  <div class="st-garde" id="f-garde"></div>
  <div class="r"><button class="b p" onclick="saveSt()">Garder ici</button><button class="b" onclick="clrSt()">Effacer</button></div>
  <div class="r"><button class="b" onclick="show('sceau')">← Sceau</button><button class="b" onclick="show('out')">Sortir</button></div>
</div>
<div class="view" id="v-ecr">
  <h2 style="font-size:1.1rem;color:#b8b2a4;letter-spacing:.08em;margin-bottom:.3rem;font-weight:400">Écritoire</h2>
  <div style="font-size:.8rem;color:#5a5347;margin-bottom:1.2rem">Texte local. Rien n'est envoyé ailleurs.</div>
  <textarea class="ecr-ta" id="ecr-ta" placeholder="Écris ce qui vient. Un écran, pas un roman."></textarea>
  <div class="ecr-meta" id="ecr-meta">0 caractères</div>
  <div class="r"><button class="b p" onclick="saveEcr()">Garder ici</button><button class="b" onclick="clrEcr()">Effacer</button></div>
  <div class="r"><button class="b" onclick="show('sceau')">← Sceau</button><button class="b" onclick="show('out')">Sortir</button></div>
</div>
<div class="view" id="v-mem">
  <h2 style="font-size:1.1rem;color:#b8b2a4;letter-spacing:.08em;margin-bottom:.3rem;font-weight:400">Mémoire sobre</h2>
  <div style="font-size:.8rem;color:#5a5347;margin-bottom:1.2rem">Tes textes, ici. Pas de feed, pas de classement.</div>
  <div class="mem-list" id="mem-list"></div>
  <div class="r"><button class="b" onclick="exportJSON()">Exporter</button><button class="b d" id="clr-all" onclick="confirmClear()">Tout effacer</button></div>
  <div class="r"><button class="b" onclick="show('sceau')">← Sceau</button><button class="b" onclick="show('out')">Sortir</button></div>
</div>
<div class="view" id="v-about">
  <h2 style="font-size:1.15rem;color:#b8b2a4;letter-spacing:.1em;margin-bottom:1.2rem;font-weight:400">À propos</h2>
  <div class="about-p">
    <p>Forteresse est un lieu, pas un maître.</p>
    <p>Rien ici ne te juge, ne te note, ne te retient.</p>
    <p>Tout ce que tu écris reste sur ton appareil.</p>
  </div>
  <ul class="about-list">
    <li>Créer sans mentir</li><li>Agir sans forcer</li><li>Pouvoir sans écraser</li>
    <li>Se tromper sans s'y enfermer</li><li>Recevoir sans posséder</li><li>Espérer sans imposer</li>
  </ul>
  <div class="r"><button class="b" onclick="show('sceau')">← Sceau</button></div>
</div>
<div class="view" id="v-out">
  <p style="font-size:1rem;color:#b8b2a4;line-height:2;margin-bottom:2rem">Tu peux repos.<br><br>Revenir n'est pas échouer.<br>Sortir n'est pas abandonner.</p>
  <div class="r"><button class="b p" onclick="show('sceau')">Revenir au sceau</button><button class="b" onclick="exit()">Repos</button></div>
</div>
<div class="nav" id="nav">
  <button onclick="show('sceau')">Sceau</button><button onclick="show('ecr')">Écritoire</button>
  <button onclick="show('mem')">Mémoire</button><button onclick="show('about')">À propos</button>
</div>
<div class="toast" id="toast"></div>
<script>
var S={repentance:{n:"Repentance",w:"\u25BD",p:"Reconna\u00EEtre. Corriger. Apprendre.\nNommer l\u2019\u00E9cart n\u2019est pas s\u2019enfermer dedans.",q:"Quel geste r\u00E9el s\u2019\u00E9carte du vrai bien \u2014 sans mensonge, sans th\u00E9\u00E2tre ?",g:"La repentance tourne. Elle ne broie pas. Tu peux t\u2019arr\u00EAter.",b:true},pardon:{n:"Pardon",w:"\u25B7",p:"Ne verrouiller personne dans sa faute \u2014 toi non plus.\nPardonner n\u2019est pas r\u00E9concilier. Ce n\u2019est pas encore faire confiance.",q:"Qui ne doit plus \u00EAtre r\u00E9duit \u00E0 sa pire heure \u2014 toi compris ?",b:false},gratitude:{n:"Gratitude",w:"\u25C1",p:"Recevoir ce qui a \u00E9t\u00E9 donn\u00E9, sans le transformer en d\u00FB.",q:"Qu\u2019est-ce qui t\u2019a \u00E9t\u00E9 donn\u00E9 aujourd\u2019hui, et que tu n\u2019as pas produit seul ?",b:false},esperance:{n:"Esp\u00E9rance",w:"\u25B3",p:"Voir encore une voie bonne. La choisir. Agir un peu.\nSans imposer cette voie \u00E0 autrui. Sans se couronner.",q:"Quelle petite voie encore possible sert le prochain mieux que ton confort ?",b:false,v:true}};
var cur=null,data=[];
try{data=JSON.parse(localStorage.getItem("ft")||"[]");}catch(e){data=[];}
function show(id){var v=document.querySelectorAll(".view");for(var i=0;i<v.length;i++)v[i].classList.remove("on");var el=document.getElementById("v-"+id);if(el)el.classList.add("on");var n=document.getElementById("nav");if(id==="silence"||id==="seuil")n.classList.remove("on");else n.classList.add("on");if(id==="mem")loadMem();}
function exit(){show("silence");setTimeout(function(){show("seuil");},2500);}
function station(k){cur=k;var s=S[k];document.getElementById("f-wg").textContent=s.w;document.getElementById("f-nm").textContent=s.n;document.getElementById("f-par").textContent=s.p;document.getElementById("f-prm").textContent=s.q;document.getElementById("f-ta").value="";document.getElementById("f-garde").classList.remove("on");show("station");}
var BIAS=[/je suis (nul|stupide|inutile|minable|path\u00E9tique)/i,/je ne vaux rien/i,/je ne m\u00E9rite (pas|rien)/i,/je suis un \u00E9chec/i,/je d\u00E9truis tout/i,/je suis incapable/i,/je suis (le|la) pire/i];
var VIG=[/je dois/i,/il faut que/i,/tous doivent/i,/c.*est la seule/i,/absolu/i,/toujours/i,/jamais/i];
function tp(t,a){for(var i=0;i<a.length;i++)if(a[i].test(t))return true;return false;}
document.addEventListener("input",function(e){if(!e.target)return;if(e.target.id==="f-ta"&&cur){var s=S[cur];var g=document.getElementById("f-garde");if(s.b&&tp(e.target.value,BIAS)){g.textContent=s.g;g.classList.add("on");}else if(s.v&&e.target.value.length>25&&tp(e.target.value,VIG)){g.textContent="L\u2019esp\u00E9rance propose. Elle n\u2019impose. Tu peux revenir au seuil d\u2019humilit\u00E9.";g.classList.add("on");}else{g.classList.remove("on");}}if(e.target.id==="ecr-ta"){document.getElementById("ecr-meta").textContent=e.target.value.length+" caractères";}});
function save(){try{localStorage.setItem("ft",JSON.stringify(data));}catch(e){}}
function saveSt(){var t=document.getElementById("f-ta").value.trim();if(!t){toast("Rien à garder. C'est bien aussi.");return;}data.push({s:S[cur].n,t:t,d:new Date().toISOString()});save();toast("Gardé ici. Rien n'est envoyé ailleurs.");document.getElementById("f-ta").value="";document.getElementById("f-garde").classList.remove("on");}
function clrSt(){document.getElementById("f-ta").value="";document.getElementById("f-garde").classList.remove("on");}
function saveEcr(){var t=document.getElementById("ecr-ta").value.trim();if(!t){toast("Rien à garder.");return;}data.push({s:"Écritoire",t:t,d:new Date().toISOString()});save();toast("Gardé ici.");document.getElementById("ecr-ta").value="";document.getElementById("ecr-meta").textContent="0 caractères";}
function clrEcr(){document.getElementById("ecr-ta").value="";document.getElementById("ecr-meta").textContent="0 caractères";}
function loadMem(){var l=document.getElementById("mem-list");if(data.length===0){l.innerHTML='<div class="mem-empty">Rien ici pour l'instant. C'est bien.</div>';return;}var s=data.slice().sort(function(a,b){return new Date(b.d)-new Date(a.d);});var h="";for(var i=0;i<s.length;i++){var e=s[i];var d=new Date(e.d);var ds=d.toLocaleDateString("fr-FR",{day:"numeric",month:"long",year:"numeric"})+" · "+d.toLocaleTimeString("fr-FR",{hour:"2-digit",minute:"2-digit"});var idx=data.indexOf(e);h+='<div class="mem-item" onclick="del('+idx+')"><div class="d">'+ds+'</div><div class="s">'+esc(e.s)+'</div><div class="p">'+esc(e.t.substring(0,180))+'</div><div class="hint">Toucher pour effacer</div></div>';}l.innerHTML=h;}
function del(idx){data.splice(idx,1);save();loadMem();toast("Effacé.");}
function confirmClear(){if(data.length===0){toast("Rien à effacer.");return;}var b=document.getElementById("clr-all");if(b.dataset.c==="1"){data=[];save();loadMem();toast("Tout effacé.");b.dataset.c="0";b.textContent="Tout effacer";}else{b.dataset.c="1";b.textContent="Confirmer ? Touche encore";setTimeout(function(){b.dataset.c="0";b.textContent="Tout effacer";},3000);}}
function exportJSON(){if(data.length===0){toast("Rien à exporter.");return;}var bl=new Blob([JSON.stringify(data,null,2)],{type:"application/json"});var u=URL.createObjectURL(bl);var a=document.createElement("a");a.href=u;a.download="forteresse-"+new Date().toISOString().slice(0,10)+".json";document.body.appendChild(a);a.click();document.body.removeChild(a);URL.revokeObjectURL(u);toast("Exporté en JSON.");}
function toast(m){var t=document.getElementById("toast");t.textContent=m;t.classList.add("on");clearTimeout(t._t);t._t=setTimeout(function(){t.classList.remove("on");},2800);}
function esc(s){return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");}
if("serviceWorker" in navigator){window.addEventListener("load",function(){navigator.serviceWorker.register("sw.js").catch(function(){});});}
setTimeout(function(){show("seuil");},2000);
</script>
</body>
</html>
```

## Ce que tu dois faire

1. **Valide** le code — parcours le flux, corrige les bugs.
2. **Ajoute** `manifest.json` et `sw.js` (PWA offline).
3. **Améliore** : aria-label, contraste WCAG, responsive 320px, icônes PNG 192/512.
4. **Ajoute** export CSV en plus du JSON.
5. **Déploie** : instructions Netlify Drop + GitHub Pages.
6. Produis un `README.md` sobre.

Ne change ni le ton, ni les textes, ni les principes.
