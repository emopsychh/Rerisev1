import { apiRequest } from "./client";

export async function fetchPartnerDashboard() {
  return apiRequest<Record<string, unknown>>("/partner/dashboard");
}

export async function fetchPartnerRanks() {
  return apiRequest("/partner/ranks");
}

export async function fetchPartnerStructure(params?: { leg?: string; depth?: number }) {
  const q = new URLSearchParams();
  if (params?.leg) q.set("leg", params.leg);
  if (params?.depth) q.set("depth", String(params.depth));
  const suffix = q.toString() ? `?${q}` : "";
  return apiRequest(`/partner/structure${suffix}`);
}

export async function fetchInvited() {
  return apiRequest("/partner/invited");
}

export async function renewPartner() {
  return apiRequest("/partner/renew", { method: "POST" });
}
