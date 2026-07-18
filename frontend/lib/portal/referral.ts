export const REFERRAL_CODE_STORAGE_KEY = "rerise-referral-code";

export function inviteUrlFromReferralCode(code: string | null | undefined): string {
  const trimmed = (code || "").trim();
  if (!trimmed) return "";
  if (typeof window !== "undefined" && window.location?.origin) {
    return `${window.location.origin}/join/${encodeURIComponent(trimmed)}`;
  }
  return `https://systema.site/join/${encodeURIComponent(trimmed)}`;
}

export function storeReferralCode(code: string) {
  const trimmed = code.trim();
  if (!trimmed || typeof window === "undefined") return;
  try {
    // localStorage переживает редиректы надёжнее sessionStorage
    localStorage.setItem(REFERRAL_CODE_STORAGE_KEY, trimmed);
    sessionStorage.setItem(REFERRAL_CODE_STORAGE_KEY, trimmed);
  } catch {
    /* ignore quota / private mode */
  }
}

export function readStoredReferralCode(): string {
  if (typeof window === "undefined") return "";
  try {
    return (
      localStorage.getItem(REFERRAL_CODE_STORAGE_KEY)?.trim() ||
      sessionStorage.getItem(REFERRAL_CODE_STORAGE_KEY)?.trim() ||
      ""
    );
  } catch {
    return "";
  }
}

export function clearStoredReferralCode() {
  if (typeof window === "undefined") return;
  try {
    localStorage.removeItem(REFERRAL_CODE_STORAGE_KEY);
    sessionStorage.removeItem(REFERRAL_CODE_STORAGE_KEY);
  } catch {
    /* ignore */
  }
}

/** Код из URL ?code= / пути /join/… / storage — для отправки на API. */
export function resolveReferralCodeForSubmit(explicit?: string | null): string {
  const fromArg = (explicit || "").trim();
  if (fromArg) return fromArg;
  if (typeof window === "undefined") return "";
  try {
    const q = new URLSearchParams(window.location.search).get("code");
    if (q?.trim()) return q.trim();
  } catch {
    /* ignore */
  }
  return readStoredReferralCode();
}
