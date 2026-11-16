/** Audit vérifiable; ne démontre aucune fidélité biblique. */
export function auditMerkabah(g) {
 const n=g.nodes||[],e=g.edges||[],s=g.sources||[],f=[];
 const add=(code,level,count,detail)=>f.push({code,level,count,detail});
 const ids=new Set(n.map(x=>x.id)),ss=new Set(s.map(x=>x.id));
 if(ids.size!==n.length)add("DUPLICATE_NODE_IDS","BLOCKER",n.length-ids.size,"IDs en double");
 const o=e.filter(x=>!ids.has(x.from)||!ids.has(x.to));
 if(o.length)add("ORPHAN_EDGES","BLOCKER",o.length,"Relations orphelines");
 const ns=n.filter(x=>!ss.has(x.source)),es=e.filter(x=>!ss.has(x.source));
 if(ns.length)add("UNDECLARED_NODE_SOURCES","MAJOR",ns.length,"Sources de nœuds non déclarées");
 if(es.length)add("UNDECLARED_EDGE_SOURCES","MAJOR",es.length,"Sources de relations non déclarées");
 const noStatus=[...n,...e].filter(x=>!x.status);
 if(noStatus.length)add("UNLABELED_ASSERTIONS","MAJOR",noStatus.length,"Statuts épistémiques manquants");
 for(const [type,want] of [["living_being",4],["wheel_within_wheel",4]]) {
  const got=n.filter(x=>x.type===type).length;
  if(got!==want)add("CARDINALITY_"+type.toUpperCase(),"BLOCKER",Math.abs(got-want),`Attendu ${want}, trouvé ${got}`);
 }
 const rel=(id,type)=>e.filter(x=>x.from===id&&x.type===type).map(x=>x.to);
 for(let i=1;i<=4;i++) {
  const c=`cherub_${i}`,w=`wheel_${i}`,faces=rel(c,"has_face"),wings=rel(c,"has_wing");
  const forms=faces.map(id=>n.find(x=>x.id===id)?.form);
  if(faces.length!==4||faces.some(id=>!ids.has(id))||
      forms.slice().sort().join("|")!=="eagle|human|lion|ox")add("FACES_"+i,"BLOCKER",1,"Faces complètes distinctes attendues");
  if(wings.length!==4||new Set(wings).size!==4||wings.some(id=>!ids.has(id)))add("WINGS_"+i,"BLOCKER",1,"Ailes complètes distinctes attendues");
  if(rel(c,"beside").length!==1||rel(c,"beside")[0]!==w||
     rel(w,"moves_with").length!==1||rel(w,"moves_with")[0]!==c)add("WHEEL_PAIR_"+i,"BLOCKER",1,"Couplage incomplet");
 }
 if(g.status!=="PROPOSED_NOT_VALIDATED")add("MODEL_STATUS","MAJOR",1,"Statut non prouvé");
 return {version:g.version,status:g.status,counts:{nodes:n.length,edges:e.length,sources:s.length},findings:f,verdict:f.some(x=>x.level==="BLOCKER"||x.level==="MAJOR")?"REVIEW_REQUIRED":"STRUCTURE_ONLY_NOT_BIBLICAL_VALIDATION"};
}
