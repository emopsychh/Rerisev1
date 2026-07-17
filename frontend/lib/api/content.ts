import { apiRequest } from "./client";

export async function fetchMaterials(params?: { category?: string; search?: string }) {
  const q = new URLSearchParams();
  if (params?.category) q.set("category", params.category);
  if (params?.search) q.set("search", params.search);
  const suffix = q.toString() ? `?${q}` : "";
  return apiRequest(`/materials${suffix}`);
}

export async function fetchMaterialGroup(id: number) {
  return apiRequest(`/materials/groups/${id}`);
}

export async function fetchChats() {
  return apiRequest("/chats");
}
