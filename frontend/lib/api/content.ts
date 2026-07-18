import { apiRequest } from "./client";

export async function fetchMaterials(params?: { category?: string; search?: string }) {
  const q = new URLSearchParams();
  if (params?.category) q.set("category", params.category);
  if (params?.search) q.set("search", params.search);
  const suffix = q.toString() ? `?${q}` : "";
  return apiRequest(`/materials${suffix}`);
}

export async function fetchMaterialGroup(id: number) {
  return apiRequest<{
    id: number;
    title: string;
    files: Array<{
      id: number;
      title: string;
      format: string;
      file_url: string;
      file_size: number;
    }>;
  }>(`/materials/groups/${id}`);
}

export function materialFileDownloadPath(fileId: number) {
  return `/materials/files/${fileId}/download`;
}

export async function fetchChats() {
  return apiRequest("/chats");
}
