/** Vérificateur extérieur des octets pointés par des événements SOURCE VIGIE-V1.
 * Aucun réseau, aucune mutation du journal, aucune revendication d'authenticité Drive.
 */
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {inspect} from './verify.mjs';

const sha256 = bytes => createHash('sha256').update(bytes).digest('hex');
const fail = code => Object.assign(new Error(code), {code});
const isStr = v => typeof v === 'string' && v.trim().length>0;

/**
 * @param {object} journal VIGIE-V1, doit d'abord passer inspect()
 * @param {Array<{id:string,sourceRef:string,bytes:Uint8Array}>} files octets fournis en dehors du journal
 * @returns {object} CONCORDANCE_OCTETS_NON_AUTHENTIFIANTE ou refus précis
 */
export function bindSources(journal, files) {
  try {
    const base=inspect(journal);
    if(!base.ok)throw fail('JOURNAL_'+base.code);
    if(!Array.isArray(files))throw fail('LIENS_FICHIERS_MANQUANTS');
    const sourceEvents=journal.events.filter(e=>e.type==='SOURCE');
    if(sourceEvents.length===0)throw fail('SOURCES_ABSENTES');
    const supplied=new Map();
    for(const f of files){
      if(!f || !isStr(f.id) || !isStr(f.sourceRef) || !(f.bytes instanceof Uint8Array))throw fail('LIEN_INVALIDE');
      if(supplied.has(f.id))throw fail('LIEN_DUPLIQUE');
      supplied.set(f.id,f);
    }
    if(supplied.size!==sourceEvents.length)throw fail('NOMBRE_SOURCES_INCOHERENT');
    const observed=[];
    for(const {data:s} of sourceEvents){
      if(!supplied.has(s.id))throw fail('SOURCE_SANS_OCTETS');
      const f=supplied.get(s.id);
      if(s.sourceRef!==f.sourceRef)throw fail('SOURCE_REFERENCE_DIFFERENTE');
      if(s.bytes!==f.bytes.byteLength)throw fail('SOURCE_TAILLE_DIFFERENTE');
      const measured=sha256(f.bytes);
      if(s.sha256!==measured)throw fail('SOURCE_EMPREINTE_DIFFERENTE');
      observed.push({id:s.id,sourceRef:s.sourceRef,sha256:measured,bytes:f.bytes.byteLength});
    }
    return {ok:true,code:'CONCORDANCE_OCTETS_NON_AUTHENTIFIANTE',observed,sourceCount:observed.length,
      journalTip:base.tip,identity:'NON_VERIFIEE',authenticity:'NON_ETABLIE',
      modelAuthority:'none',authorization:'NOT_ASSESSED',canon:'NON_ADOPTE'};
  } catch(e){return {ok:false,code:e.code||'VERIFICATION_IMPOSSIBLE',identity:'NON_VERIFIEE',authorization:'NOT_ASSESSED'};}
}

if(process.argv[1] && import.meta.url===new URL('file://'+process.argv[1]).href){
  if(process.argv.length!==4){console.error('Usage: node bind-sources.mjs journal.json sources-manifest.json');process.exit(2)}
  try {
    const journal=JSON.parse(readFileSync(process.argv[2],'utf8'));
    const manifest=JSON.parse(readFileSync(process.argv[3],'utf8'));
    if(manifest?.schema!=='VIGIE-SOURCE-MAP-V1' || !Array.isArray(manifest.files))throw fail('MANIFESTE_INVALIDE');
    const files=manifest.files.map(f=>{
      if(!f || !isStr(f.id) || !isStr(f.sourceRef) || !isStr(f.path))throw fail('MANIFESTE_INVALIDE');
      return {id:f.id,sourceRef:f.sourceRef,bytes:readFileSync(f.path)};
    });
    const report=bindSources(journal,files);console.log(JSON.stringify(report,null,2));
    if(!report.ok)process.exitCode=1;
  } catch(e){console.error(JSON.stringify({ok:false,code:e.code||'ERREUR_IO_OU_MANIFESTE',message:String(e.message)}));process.exitCode=2;}
}
