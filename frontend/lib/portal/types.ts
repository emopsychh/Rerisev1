export type SectionId = "home" | "cabinet" | "workspace" | "courses" | "library" | "labor" | "chats" | "marketing" | "partners" | "crm" | "marketplace" | "wallet" | "profile";
export type TFn = (value: string) => string;
export type NotifyFn = (message: string) => void;
export type MarketTab = "packages" | "tokens";
export type TelegramResourceId = "partnerChat" | "leadersChat" | "onboardingChat" | "contentChat" | "supportChat" | "marketingChannel";
export type DetailView =
  | { type: "course"; slug: string; title?: string; returnTo: SectionId }
  | { type: "material"; title: string; returnTo: SectionId };
export type CrmDeal = {
  id: string;
  name: string;
  source: string;
  task: string;
  time: string;
  phone: string;
  contact: string;
  note: string;
  email?: string;
  createdAt?: string;
};
export type CrmColumn = {
  id: string;
  title: string;
  color: string;
  deals: CrmDeal[];
};
export type MarketOffer = {
  kind: "program" | "package" | "tokens";
  title: string;
  price: string;
  pv: string;
  text: string;
  features: string[];
  productId?: string;
};
export type CrmTimelineNote = {
  id: string;
  text: string;
  time: string;
};
export type CourseLessonItem = { title: string; duration: string };
export type CourseModuleItem = { title: string; description: string; lessons: CourseLessonItem[] };
export type TeamPartnerNode = {
  id: string;
  name: string;
  initial: string;
  rank: string;
  sponsorId: string | null;
  branchId: "left" | "right" | "personal";
  level: string;
  active: boolean;
  children: readonly [string | null, string | null];
  teamSize: number;
  activeTeam: number;
  remainingPv: number;
  telegram: string;
  phone: string;
};
export type WalletPeriod = "today" | "yesterday" | "week" | "month" | "year" | "all" | "custom";
export type WalletTransactionType = "all" | "income" | "expense";
export type WalletTransactionCategory = "personal" | "binary" | "matching" | "renewal" | "fast_start" | "withdrawal" | "subscription";
