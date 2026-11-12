export const fixed=(v:unknown,n=3)=>Number(v||0).toFixed(n);export const pct=(v:unknown)=>(Number(v||0)*100).toFixed(1)+"%";
