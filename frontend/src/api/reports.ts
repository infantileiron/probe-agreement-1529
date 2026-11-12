import {request} from "./client";export const fetchReports=()=>request("/reports");export const createReports=(body:unknown)=>request("/reports","POST",body);
