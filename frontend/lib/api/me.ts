import { apiRequest } from "./client";
import type { Profile } from "./types";

export async function fetchProfile() {
  return apiRequest<Profile>("/me/profile");
}

export async function updateProfile(payload: Partial<Profile>) {
  return apiRequest<Profile>("/me/profile", { method: "PATCH", body: payload });
}

export async function fetchInviteLink() {
  const data = await apiRequest<{
    referral_url?: string;
    referral_code?: string;
    invite_url?: string;
    code?: string;
  }>("/me/invite-link", {
    method: "POST",
  });
  return {
    invite_url: data.invite_url || data.referral_url || "",
    code: data.code || data.referral_code || "",
  };
}

export async function fetchNotifications() {
  return apiRequest<
    Array<{
      id: number;
      type: string;
      title: string;
      body: string;
      is_read: boolean;
      created_at: string;
    }>
  >("/notifications");
}

export async function markAllNotificationsRead() {
  return apiRequest<{ marked: number }>("/notifications/read-all", {
    method: "PATCH",
  });
}

export async function markNotificationRead(id: number) {
  return apiRequest<{ is_read: boolean }>(`/notifications/${id}/read`, {
    method: "PATCH",
  });
}

export async function updateNotificationSettings(payload: {
  email_enabled?: boolean;
  push_enabled?: boolean;
}) {
  return apiRequest("/me/notifications", { method: "PATCH", body: payload });
}
