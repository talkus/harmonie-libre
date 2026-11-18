// U15.4.3 — numerical checks, not experimental results. Node.js, no dependencies.
function verifyU1543(){
 const check=(x,m)=>{if(!x)throw Error(m)};
 const rows=[];
 for(let n=1;n<=20;n++){
  let k=1,gate=0,layers=0,exp=0;
  for(let t=0;t<n;t++){gate+=2*k;layers+=2;exp+=k;k*=2}
  check(gate===2*exp&&exp===2**n-1&&layers===2*n,"counts");
  rows.push({n,controllers:k,exports:exp,gates:gate,layers,timeRatio:gate/exp});
 }
 const lambda=1000,T=1000,M=10000;
 const lower=lambda/2*Math.max(0,T-M/lambda)**2;
 check(lower===490050000,"Poisson lower bound");
 const q=.1,p=.25,e=q/(1-p+q);
 const af=(x,y)=>Math.sqrt(x*y)+Math.sqrt((1-x)*(1-y));
 const affinity=[];
 for(const n of [1,2,4,8,16,32,64,128,256,512,1024]){
   const b=Math.min(1,Math.sqrt(1-q)*af(q,e)**n+Math.sqrt(q)*af(p,e)**n);
   affinity.push({n,bound:b});
 }
 check(af(q,e)<1&&af(p,e)<1,"strict affinity");
 check(affinity[affinity.length-1].bound<.7,"vanishing bound");
 // Count exact pathwise comparisons in a slotted control model.
 // Equal initial controller, at most one completed gate per slot, fresh tokens released.
 // Direct export may be stockpiled. A recruit uses one token but creates no export.
 const slots=6;
 let histories=0,paths=0;
 for(let mask=0;mask<2**slots;mask++){
   const releases=Array.from({length:slots},(_,i)=>(mask>>i)&1);
   for(let demands=0;demands<2**slots;demands++){
     histories++;
     function walk(i,stock,exp,gen,lag,refLag,refExp){
       if(i===slots){paths++;check(lag>=refLag,"lag domination");return}
       const stockNext=stock+releases[i];
       const cumulativeDemand=Array.from({length:i+1},(_,j)=>(demands>>j)&1).reduce((a,b)=>a+b,0);
       const nextRef=refExp+releases[i]; // immediate non-generative export of every released token
       const nextRefLag=refLag+Math.max(0,cumulativeDemand-nextRef);
       for(const action of [0,1,2]){ // idle, export, recruit
         if(action&&stockNext===0)continue;
         const out=exp+(action===1?1:0);
         check(out<=nextRef,"pathwise count");
         walk(i+1,stockNext-Number(action!==0),out,gen+Number(action===2),lag+Math.max(0,cumulativeDemand-out),nextRefLag,nextRef)
       }
     }
     walk(0,0,0,1,0,0,0);
   }
 }
 const n=4,G=15,a=1,s=3;
 const witness={n,G,a,s,genTime:2*a*G+2*n*s,fixedTime:G*(a+s),genTokens:2*G,fixedTokens:G,width:16};
 check(witness.genTime===54&&witness.fixedTime===60&&witness.genTime<witness.fixedTime,"conditional example");
 return {counts:rows,poisson:{lambda,T,M,lower,upper:lambda*T*T/2},affinity,slotted:{slots,histories,paths},witness};
}
console.log(JSON.stringify(verifyU1543(),null,2));
