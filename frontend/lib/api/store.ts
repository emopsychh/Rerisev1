import { apiRequest } from "./client";

export async function fetchTariffs() {
  return apiRequest<
    Array<{
      id: string;
      name: string;
      price_usd: number;
      description: string;
      personal_bonus_cap_usd: number;
      purchase_pv_cap: number;
      binary_depth: number;
      matching_lines: number;
      initial_tokens: number;
    }>
  >("/store/tariffs", { auth: false });
}

export async function fetchTokenPacks() {
  const data = await apiRequest<{
    balance: number;
    packs: Array<{
      id: string;
      name?: string;
      price_usd: number;
      amount: number;
    }>;
  }>("/store/tokens");
  return data.packs ?? [];
}

export async function createOrder(product_id: string, order_type: string) {
  return apiRequest<{
    order_id: number;
    status: string;
    amount_usd: number;
    payment: {
      provider: string;
      payment_url: string | null;
      instructions: string;
      status: string;
    };
  }>("/store/orders", {
    method: "POST",
    body: { product_id, order_type },
  });
}

export async function fetchOrder(orderId: number) {
  return apiRequest(`/store/orders/${orderId}`);
}
