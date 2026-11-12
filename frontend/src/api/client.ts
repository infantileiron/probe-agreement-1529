export async function request<T=any>(path:string,method="GET",body?:unknown):Promise<T>{
 const token=localStorage.getItem("probe-token");const response=await fetch("/api"+path,{method,headers:{"Content-Type":"application/json",...(token?{Authorization:"Bearer "+token}:{})},body:body===undefined?undefined:JSON.stringify(body)});
 if(!response.ok){let message="请求失败";try{const error=await response.json();message=typeof error.detail==="string"?error.detail:JSON.stringify(error.detail)}catch{};throw new Error(message)}return response.json();
}
export async function downloadCsv(id:string){const r=await fetch("/api/reports/"+id+"/csv",{headers:{Authorization:"Bearer "+localStorage.getItem("probe-token")}});if(!r.ok)throw new Error("下载失败");const a=document.createElement("a");a.href=URL.createObjectURL(await r.blob());a.download="probe-calibration.csv";a.click();URL.revokeObjectURL(a.href)}
