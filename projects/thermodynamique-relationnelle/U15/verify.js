/* U15.3–U15.4: exact finite gate enumeration and ideal numerical witnesses. No dependencies. */
function verify() {
  const rows=[];
  function pareto(points){return points.filter(p=>!points.some(q=>(q[0]!==p[0]||q[1]!==p[1])&&q[0]<=p[0]&&q[1]<=p[1])).sort((a,b)=>a[0]-b[0]||a[1]-b[1]);}
  function search(m,prep) {
    const initial={s:Array.from({length:prep?1:2},()=>Array(m+1).fill(0)),p:+prep,g:+prep};
    const key=({s,p,g})=>JSON.stringify([s,p,g]);
    const queue=[initial], seen=new Set([key(initial)]), reached=new Map();
    for(let j=0;j<queue.length;j++){
      const {s,p,g}=queue[j];
      if(s.every(b=>b.slice(1).every(Boolean))) reached.set(`${p},${g}`,[p,g]);
      if(g===2*m+1) continue;
      const push=(s,cost)=>{const v={s,p:p+cost,g:g+1},k=key(v); if(v.p<=m+2&&!seen.has(k)){seen.add(k);queue.push(v);}};
      for(const q of [0,1])push(s.map(b=>[q,...b.slice(1)]),q);
      for(let i=1;i<=m;i++){
        push(s.map(b=>{const a=b.slice();[a[0],a[i]]=[a[i],a[0]];return a;}),0);
        for(const q of [0,1]){const a=s.map(b=>b.slice());a[0][i]=q;push(a,q);}
      }
    }
    return {front:pareto([...reached.values()]),states:seen.size};
  }
  const comb=(n,k)=>{let v=1;for(let i=1;i<=k;i++)v=v*(n-i+1)/i;return v;};
  const totalVariation=(m,q,p)=>Array.from({length:m+1},(_,j)=>comb(m,j)*Math.abs(q**j*(1-q)**(m-j)-p**j*(1-p)**(m-j))).reduce((a,b)=>a+b,0)/2;
  const assert=(ok,msg)=>{if(!ok)throw Error(msg);};
  for(let m=1;m<=5;m++){
    const a=search(m,false),b=search(m,true);
    assert(JSON.stringify(a.front)===JSON.stringify([[m,2*m]]),"reference");
    assert(JSON.stringify(b.front)===JSON.stringify([[m+1,m+1]]),"activation");
    rows.push({m,reference:a.front,prepared:b.front,states:a.states+b.states,error_H0:.01*totalVariation(m,.1,.5),error_Hnonzero:.01*totalVariation(m,.1,.3)});
  }
  const beta=1, gap=Math.log(7/3),p=1/(1+Math.exp(beta*gap)),q=.1,eta=.01;
  assert(Math.abs(p-.3)<1e-12,"Gibbs p");
  const H=[0,gap,gap,2*gap]; const swap=[0,2,1,3];
  assert(swap.every((j,i)=>H[j]===H[i]),"energy-conserving SWAP");
  // Control=0 means SWAP; control=1 means identity. Same two-level gaps.
  const energies=Array.from({length:8},(_,i)=>gap*((i>>2&1)+(i>>1&1)+(i&1)));
  const fredkin=[0,2,1,3,4,5,6,7];
  assert(fredkin.every((j,i)=>energies[j]===energies[i]),"energy-conserving Fredkin");
  const D=(q,p)=>q*Math.log(q/p)+(1-q)*Math.log((1-q)/(1-p));
  const m=4;
  const therm={beta,gap,p,q,eta,m,trace_error:eta*totalVariation(m,q,p),reference_error_lower_bound:(1-p)*(0)+p*(p-q),resource_free_energy_over_kBT:m*D(q,p)+D(eta,p),controller_reverse_relative_entropy:D(p,eta),controller_support:-Math.log(Math.min(eta/p,(1-eta)/(1-p)))};
  assert(therm.trace_error<.02&&therm.reference_error_lower_bound>.02,"finite error separation");
  const growth=[];
  for(const exponent of [0,.5,1]){
    let k=10,G=0,L=0,P=0;
    for(let t=0;t<8;t++){const targets=2*k;G+=targets/2;P+=targets;L+=Math.ceil(targets/Math.max(1,Math.floor(k**exponent)));k+=targets/2;}
    assert(k+G===10+P,"purity inventory");
    growth.push({exponent,k,exported:G,depth:L,pure_inputs:P,targets_per_depth:G/L,export_per_input:G/P});
  }
  return {rows,visited:rows.reduce((a,b)=>a+b.states,0),therm,growth};
}
console.log(JSON.stringify(verify(),null,2));
