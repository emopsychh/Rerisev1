import { PARTNER_TIERS } from "../marketing-plan";
import type { NotifyFn, TelegramResourceId, TFn } from "./types";

export const AI_BOX_BOT_URL = "https://t.me/app_systema_bot";
export const TELEGRAM_LINKS: Record<TelegramResourceId, string | null> = {
  partnerChat: null,
  leadersChat: null,
  onboardingChat: null,
  contentChat: null,
  supportChat: null,
  marketingChannel: null,
};

export function openTelegramResource(resource: TelegramResourceId, label: string, notify: NotifyFn, t: TFn) {
  const url = TELEGRAM_LINKS[resource];
  if (!url) {
    notify(`${t(label)} · ${t("Telegram-ссылка будет добавлена перед запуском")}`);
    return;
  }
  window.open(url, "_blank", "noopener,noreferrer");
}

export function formatApiDate(value: unknown, fallback = "—"): string {
  if (!value) return fallback;
  const date = new Date(String(value));
  if (Number.isNaN(date.getTime())) return fallback;
  return date.toLocaleDateString("ru-RU", { day: "2-digit", month: "2-digit", year: "numeric" });
}

export function describeCurrentDevice(): string {
  if (typeof navigator === "undefined") return "Текущий браузер";
  const ua = navigator.userAgent;
  let browser = "Браузер";
  if (/Edg\//.test(ua)) browser = "Edge";
  else if (/Chrome\//.test(ua) && !/Chromium\//.test(ua)) browser = "Chrome";
  else if (/Firefox\//.test(ua)) browser = "Firefox";
  else if (/Safari\//.test(ua) && !/Chrome\//.test(ua)) browser = "Safari";

  let os = "устройство";
  if (/Windows/i.test(ua)) os = "Windows";
  else if (/Mac OS X|Macintosh/i.test(ua)) os = "macOS";
  else if (/Android/i.test(ua)) os = "Android";
  else if (/iPhone|iPad/i.test(ua)) os = "iOS";
  else if (/Linux/i.test(ua)) os = "Linux";

  return `${browser} · ${os}`;
}

export function formatUsd(value: number, fallback = "$0"): string {
  if (!Number.isFinite(value)) return fallback;
  return `$${value.toLocaleString("ru-RU", { maximumFractionDigits: 0 })}`;
}

export function tariffDisplayName(tariffId?: string | null): string {
  if (!tariffId) return "";
  return PARTNER_TIERS.find((item) => item.id === tariffId)?.name ?? tariffId;
}

export function formatLeadTime(value: unknown): string {
  if (!value) return "Сегодня";
  const raw = String(value);
  if (raw.includes("T")) {
    const date = new Date(raw);
    if (!Number.isNaN(date.getTime())) {
      return date.toLocaleString("ru-RU", { day: "numeric", month: "long", hour: "2-digit", minute: "2-digit" });
    }
  }
  return raw;
}

export function formatCrmPhone(value: string) {
  let digits = value.replace(/\D/g, "");
  if (digits.startsWith("8")) digits = `7${digits.slice(1)}`;
  if (!digits.startsWith("7")) digits = `7${digits}`;
  digits = digits.slice(0, 11);

  const national = digits.slice(1);
  let formatted = "+7";
  if (national.length > 0) formatted += ` (${national.slice(0, 3)}`;
  if (national.length >= 3) formatted += ")";
  if (national.length > 3) formatted += ` ${national.slice(3, 6)}`;
  if (national.length > 6) formatted += `-${national.slice(6, 8)}`;
  if (national.length > 8) formatted += `-${national.slice(8, 10)}`;
  return formatted;
}

export const PAYOUT_ADDRESS_STORAGE_KEY = "rerise-usdt-payout-address";
export const hasUsdtAddress = (value: string) => value.trim().length >= 8 && !/\s/.test(value.trim());
export const maskWalletAddress = (value: string) => (value ? `${value.slice(0, 6)}••••${value.slice(-5)}` : "Не указан");
