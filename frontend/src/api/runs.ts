import {request} from "./client";export const fetchRuns=()=>request("/runs");export const createRuns=(body:unknown)=>request("/runs","POST",body);
