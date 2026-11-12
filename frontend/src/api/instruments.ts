import {request} from "./client";export const fetchInstruments=()=>request("/instruments");export const createInstruments=(body:unknown)=>request("/instruments","POST",body);
