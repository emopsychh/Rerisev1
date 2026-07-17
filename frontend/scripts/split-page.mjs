/**
 * Mechanical split of app/page.tsx → lib/portal + components/portal
 * Run: node scripts/split-page.mjs
 */
import fs from "fs";
import path from "path";

const ROOT = path.resolve(import.meta.dirname, "..");
const SRC = path.join(ROOT, "app", "page.tsx");
const lines = fs.readFileSync(SRC, "utf8").split(/\r?\n/);

function slice(start, end) {
  return lines.slice(start - 1, end).join("\n");
}

function exportTopLevel(code) {
  return code
    .replace(/^const /gm, "export const ")
    .replace(/^function /gm, "export function ")
    .replace(/^type /gm, "export type ");
}

function write(rel, content) {
  const full = path.join(ROOT, rel);
  fs.mkdirSync(path.dirname(full), { recursive: true });
  const out = content.replace(/\n+$/, "") + "\n";
  fs.writeFileSync(full, out, "utf8");
  console.log("wrote", rel, "(" + out.split("\n").length + " lines)");
}

// ========== types ==========
write(
  "lib/portal/types.ts",
  `export type SectionId = "home" | "cabinet" | "workspace" | "courses" | "library" | "labor" | "chats" | "marketing" | "partners" | "crm" | "marketplace" | "wallet" | "profile";
export type Lang = "ru" | "en" | "es";
export type TFn = (value: string) => string;
export type NotifyFn = (message: string) => void;
export type MarketTab = "packages" | "tokens";
export type TelegramResourceId = "partnerChat" | "leadersChat" | "onboardingChat" | "contentChat" | "supportChat" | "marketingChannel";
export type DetailView =
  | { type: "course"; title: string; returnTo: SectionId }
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
`,
);

// ========== i18n ==========
write(
  "lib/portal/i18n.ts",
  `import type { Lang } from "./types";

${exportTopLevel(
    [
      slice(133, 770),
      slice(772, 1309),
      slice(1311, 1848),
      slice(1850, 1899),
      slice(1901, 1950),
      slice(1952, 1998),
      slice(2000, 2046),
      slice(2048, 2050),
    ].join("\n\n"),
  )}
`,
);

// ========== format ==========
write(
  "lib/portal/format.ts",
  `import { CURRENT_DEMO_TIER, PARTNER_TIERS } from "../marketing-plan";
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

${exportTopLevel(slice(2062, 2086))}

${exportTopLevel(slice(2096, 2106))}

${exportTopLevel(slice(2548, 2562))}

export const PAYOUT_ADDRESS_STORAGE_KEY = "rerise-usdt-payout-address";
export const hasUsdtAddress = (value: string) => value.trim().length >= 8 && !/\\s/.test(value.trim());
export const maskWalletAddress = (value: string) => (value ? \`\${value.slice(0, 6)}••••\${value.slice(-5)}\` : "Не указан");
`,
);

// ========== mock-data ==========
write(
  "lib/portal/mock-data.ts",
  `"use client";

import {
  Bot,
  BriefcaseBusiness,
  Brush,
  Camera,
  CircleUserRound,
  FileText,
  Handshake,
  Home,
  Images,
  Library,
  MessageSquareText,
  MessagesSquare,
  Play,
  Rocket,
  ShoppingBag,
  Sparkles,
  SquareKanban,
  Users,
  Video,
  WandSparkles,
  WalletCards,
  Workflow,
} from "lucide-react";
import { PARTNER_TIERS, QUICK_START_RULES } from "../marketing-plan";
import type { CourseModuleItem, CrmColumn, Lang, SectionId, TeamPartnerNode } from "./types";

${exportTopLevel(
    [
      slice(127, 131),
      slice(2168, 2198),
      slice(2200, 2525),
      slice(4077, 4149),
      slice(4506, 4521),
    ].join("\n\n"),
  )}
`,
);

// ========== routing ==========
write(
  "lib/portal/routing.ts",
  `import type { MarketOffer, MarketTab, SectionId, TFn } from "./types";
import { accessPackages, marketPrograms, tokenPacks } from "./mock-data";

${exportTopLevel(slice(2574, 2701))}

${exportTopLevel(slice(3270, 3287))}
`,
);

// ========== mappers ==========
write(
  "lib/portal/mappers.ts",
  `"use client";

import { BookOpen, FileText } from "lucide-react";
import type { CourseModuleItem, CrmColumn, CrmDeal } from "./types";
import { chatGptCurriculum, courseTopicSeeds, courses, crmColumns, materialCards } from "./mock-data";
import { formatApiDate, formatLeadTime } from "./format";
import { routeSlug } from "./routing";

${exportTopLevel(slice(2088, 2094))}

${exportTopLevel(slice(2108, 2166))}

${exportTopLevel(slice(2527, 2540))}

${exportTopLevel(slice(2564, 2572))}

${exportTopLevel(slice(4151, 4175))}
`,
);

write(
  "lib/portal/index.ts",
  `export * from "./types";
export * from "./i18n";
export * from "./format";
export * from "./mock-data";
export * from "./routing";
export * from "./mappers";
`,
);

// ========== shared ==========
write(
  "components/portal/shared/PageShell.tsx",
  `${exportTopLevel(slice(6386, 6392))}
`,
);

write(
  "components/portal/shared/PortalDialog.tsx",
  `"use client";

import { X } from "lucide-react";

${exportTopLevel(slice(6394, 6429))}
`,
);

write(
  "components/portal/shared/ProgressItem.tsx",
  `${exportTopLevel(slice(3686, 3704))}
`,
);

// ========== dialogs ==========
write(
  "components/portal/dialogs/InviteDialog.tsx",
  `"use client";

import { Copy, MessageSquareText, QrCode, Send } from "lucide-react";
import type { NotifyFn, TFn } from "../../../lib/portal/types";
import { PortalDialog } from "../shared/PortalDialog";

${exportTopLevel(slice(6431, 6482))}
`,
);

write(
  "components/portal/dialogs/RenewalDialog.tsx",
  `"use client";

import { useState } from "react";
import { CheckCircle2, ChevronRight, RefreshCw } from "lucide-react";
import { CURRENT_DEMO_TIER, SUBSCRIPTION_RULES } from "../../../lib/marketing-plan";
import type { NotifyFn, TFn } from "../../../lib/portal/types";
import { PortalDialog } from "../shared/PortalDialog";

${exportTopLevel(slice(6484, 6535))}
`,
);

write(
  "components/portal/dialogs/StatusLadderDialog.tsx",
  `"use client";

import { useState } from "react";
import { Check, ChevronRight, Info, Trophy } from "lucide-react";
import { PARTNER_RANKS, QUALIFICATION_PERIOD, RANK_QUALIFICATION_RULES } from "../../../lib/marketing-plan";
import type { TFn } from "../../../lib/portal/types";
import { PortalDialog } from "../shared/PortalDialog";

${exportTopLevel(slice(6537, 6598))}
`,
);

console.log("phase1 lib+shared+dialogs done — components next via phase2");
