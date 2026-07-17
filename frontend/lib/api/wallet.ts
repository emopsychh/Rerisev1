import { apiRequest } from "./client";

export async function fetchWallet() {
  return apiRequest<{
    balance: {
      available_usd: number;
      pending_usd: number;
      total_earned_usd: number;
    };
    adjustment_debt_usd: number;
    saved_address: { address: string; network: string } | null;
    withdrawal_limits: { min_usd: number; max_per_request_usd: number };
    recent_transactions: Array<Record<string, unknown>>;
  }>("/wallet");
}

export async function fetchWalletTransactions(params?: { type?: string }) {
  const q = params?.type ? `?type=${encodeURIComponent(params.type)}` : "";
  return apiRequest(`/wallet/transactions${q}`);
}

export async function createWithdraw(payload: {
  amount_usd: string | number;
  usdt_address: string;
  network: string;
}) {
  return apiRequest("/wallet/withdraw", { method: "POST", body: payload });
}

export async function saveWalletAddress(payload: { address: string; network: string }) {
  return apiRequest("/wallet/address", { method: "PUT", body: payload });
}
