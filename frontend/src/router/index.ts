import {ref} from 'vue';
function read(){const [path,query='']=location.hash.replace(/^#/,'').split('?');return {path:path||'/',query:new URLSearchParams(query)}}
const initial=read();export const route=ref(initial);window.addEventListener('hashchange',()=>{route.value=read()});export function go(path:string){location.hash='#'+path}
