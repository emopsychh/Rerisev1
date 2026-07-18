export const REFERRAL_CODE_STORAGE_KEY = "rerise-referral-code";

export function inviteUrlFromReferralCode(code: string | null | undefined): string {
  const trimmed = (code || "").trim();
  if (!trimmed) return "";
  if (typeof window !== "undefined" && window.location?.origin) {
    return `${window.location.origin}/join/${trimmed}`;
  }
  return `rerise.app/join/${trimmed}`;
}

export function storeReferralCode(code: string) {
  const trimmed = code.trim();
  if (!trimmed || typeof window === "undefined") return;
  try {
    sessionStorage.setItem(REFERRAL_CODE_STORAGE_KEY, trimmed);
  } catch {
    /* ignore quota / private mode */
  }
}

export function readStoredReferralCode(): string {
  if (typeof window === "undefined") return "";
  try {
    return sessionStorage.getItem(REFERRAL_CODE_STORAGE_KEY)?.trim() || "";
  } catch {
    return "";
  }
}

export function clearStoredReferralCode() {
  if (typeof window === "undefined") return;
  try {
    sessionStorage.removeItem(REFERRAL_CODE_STORAGE_KEY);
  } catch {
    /* ignore */
  }
}
