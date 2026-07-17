import { apiRequest } from "./client";

export async function fetchCrmKanban() {
  return apiRequest<{
    stages: Array<{
      slug: string;
      name: string;
      color: string;
      leads: Array<Record<string, unknown>>;
    }>;
  }>("/crm/leads");
}

export async function createLead(payload: Record<string, unknown>) {
  return apiRequest("/crm/leads", { method: "POST", body: payload });
}

export async function updateLead(id: number, payload: Record<string, unknown>) {
  return apiRequest(`/crm/leads/${id}`, { method: "PATCH", body: payload });
}

export async function deleteLead(id: number) {
  return apiRequest(`/crm/leads/${id}`, { method: "DELETE" });
}
