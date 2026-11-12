import {request} from "./client";export const fetchStudies=()=>request("/studies");export const createStudies=(body:unknown)=>request("/studies","POST",body);
