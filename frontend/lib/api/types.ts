export type ApiErrorBody = {
  code: string;
  message: string;
  details?: Record<string, unknown>;
};

export class ApiError extends Error {
  code: string;
  status: number;
  details: Record<string, unknown>;

  constructor(status: number, body: ApiErrorBody) {
    super(body.message || "API error");
    this.name = "ApiError";
    this.status = status;
    this.code = body.code || "ERROR";
    this.details = body.details || {};
  }
}

export type TokenPair = {
  access_token: string;
  refresh_token: string;
};

export type AuthUser = {
  id: number;
  email: string;
  public_id: string;
};

export type MeUser = {
  id: number;
  email: string;
  phone: string | null;
  public_id: string;
  first_name: string;
  last_name: string;
  avatar_url: string;
  language: string;
  is_partner: boolean;
  subscription: Record<string, unknown> | null;
  unread_notifications: number;
};

export type Profile = {
  first_name: string;
  last_name: string;
  avatar_url: string | null;
  country: string;
  city: string;
  language: string;
  public_id: string;
  phone?: string | null;
  email?: string;
  partner?: {
    tariff_id?: string;
    tariff_name?: string;
    is_active?: boolean;
    activity_until?: string;
    current_rank_name?: string;
  } | null;
  notifications?: {
    email_enabled?: boolean;
    push_enabled?: boolean;
  };
};
