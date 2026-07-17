import { apiRequest } from "./client";

export type HomePayload = {
  banners: Array<{
    id: number;
    title: string;
    subtitle: string;
    image_url: string;
    tags: string[];
    link_url: string | null;
  }>;
  ai_box_widget: {
    title: string;
    description: string;
    is_available: boolean;
    token_balance: number;
  };
  programs_count: number;
  next_action: {
    type: string;
    title: string;
    subtitle: string;
    link: string;
  };
  continue_learning: {
    program_slug: string;
    program_title: string;
    lesson_id: number;
    lesson_title: string;
    module_title: string;
    percent: number;
  } | null;
  partner_summary: {
    tariff_id: string;
    is_active: boolean;
    current_rank_name: string;
    can_renew: boolean;
  } | null;
  token_balance: number;
};

export async function fetchHome() {
  return apiRequest<HomePayload>("/home");
}
