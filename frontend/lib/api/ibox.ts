import { apiRequest } from "./client";

export async function fetchIboxScenarios() {
  return apiRequest<{
    scenarios: Array<Record<string, unknown>>;
    token_balance: number;
  }>("/ibox/scenarios");
}

export async function createIboxSession(payload: {
  scenario_id?: number;
  model?: string;
  title?: string;
  message?: string;
}) {
  return apiRequest<{
    session_id: number;
    message: { role: string; content: string; tokens_used: number };
    token_balance: number;
  }>("/ibox/sessions", { method: "POST", body: payload });
}

export async function sendIboxMessage(sessionId: number, content: string) {
  return apiRequest<{
    message: { role: string; content: string; tokens_used: number };
    token_balance: number;
  }>(`/ibox/sessions/${sessionId}/messages`, {
    method: "POST",
    body: { message: content },
  });
}

export async function fetchIboxSessions() {
  return apiRequest("/ibox/sessions");
}

export async function fetchIboxSession(id: number) {
  return apiRequest(`/ibox/sessions/${id}`);
}
