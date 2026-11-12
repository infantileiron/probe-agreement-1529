import {request} from "./client";export const fetchDatasets=()=>request("/datasets");export const createDatasets=(body:unknown)=>request("/datasets","POST",body);
