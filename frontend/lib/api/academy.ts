import { apiRequest } from "./client";

export async function fetchPrograms(params?: { search?: string }) {
  const q = params?.search ? `?search=${encodeURIComponent(params.search)}` : "";
  return apiRequest(`/programs${q}`);
}

export async function fetchProgram(slug: string) {
  return apiRequest(`/programs/${slug}`);
}

export async function fetchLesson(id: number) {
  return apiRequest(`/lessons/${id}`);
}

export async function startLesson(id: number) {
  return apiRequest(`/lessons/${id}/start`, { method: "POST" });
}

export async function completeLesson(id: number) {
  return apiRequest(`/lessons/${id}/complete`, { method: "POST" });
}
