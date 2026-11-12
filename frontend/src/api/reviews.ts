import {request} from "./client";export const fetchReviews=()=>request("/reviews");export const createReviews=(body:unknown)=>request("/reviews","POST",body);
