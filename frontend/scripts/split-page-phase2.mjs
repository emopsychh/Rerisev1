/**
 * Phase 2: extract views + shell from page.tsx
 * Assumes lib/portal + shared + dialogs already exist.
 * Run: node scripts/split-page-phase2.mjs
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
  return code.replace(/^function /gm, "export function ").replace(/^type /gm, "export type ");
}

function write(rel, content) {
  const full = path.join(ROOT, rel);
  fs.mkdirSync(path.dirname(full), { recursive: true });
  const out = content.replace(/\n+$/, "") + "\n";
  fs.writeFileSync(full, out, "utf8");
  console.log("wrote", rel, "(" + out.split("\n").length + " lines)");
}

const LUCIDE = `AlertTriangle, ArrowUpRight, Bell, BookOpen, Bot, BriefcaseBusiness, Brush, Camera, CalendarDays, Check, CheckCircle2, ChevronDown, ChevronLeft, ChevronRight, CircleUserRound, ClipboardPaste, Copy, CreditCard, Download, ExternalLink, FileText, Filter, Grid2X2, Headphones, History, Home, Images, Info, Library, ListChecks, Lock, MapPin, Megaphone, MessageSquareText, MessagesSquare, Play, Plus, PhoneCall, QrCode, RefreshCw, Rocket, Save, Search, Send, Settings, ShieldCheck, ShoppingBag, Smartphone, Sparkles, SquareKanban, Trophy, Video, WandSparkles, Workflow, Handshake, Users, UserPlus, WalletCards, X, Zap`;

const portalLib = `import {
  accessPackages,
  courses,
  createNewCrmLead,
  crmColumns,
  crmColumnsForRoute,
  crmColumnsFromApi,
  extractProgramList,
  formatApiDate,
  formatCrmPhone,
  formatUsd,
  hasUsdtAddress,
  languages,
  mapApiProgramToCourse,
  marketOfferFromPathname,
  marketOfferHref,
  marketProgramCourseMap,
  marketPrograms,
  maskWalletAddress,
  materialCards,
  materialsFromApi,
  mobileLabels,
  mobileMoreIds,
  mobileNavIds,
  navItems,
  openTelegramResource,
  pageTitle,
  PAYOUT_ADDRESS_STORAGE_KEY,
  promoBanners,
  routeSlug,
  sectionFromPathname,
  sectionHref,
  sectionIds,
  tariffDisplayName,
  TEAM_PARTNER_DIRECTORY,
  tokenPacks,
  translate,
  buildCourseCurriculum,
} from "../../../lib/portal";
import type {
  CrmColumn,
  CrmDeal,
  CrmTimelineNote,
  DetailView,
  Lang,
  MarketOffer,
  MarketTab,
  NotifyFn,
  SectionId,
  TelegramResourceId,
  TFn,
  WalletPeriod,
  WalletTransactionCategory,
  WalletTransactionType,
} from "../../../lib/portal";`;

function viewFile(name, start, end, extraImports = "") {
  write(
    `components/portal/views/${name}.tsx`,
    `"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { PointerEvent as ReactPointerEvent } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { ${LUCIDE} } from "lucide-react";
import { useAuth } from "../../../lib/auth/AuthProvider";
import { usePortalBackend } from "../../../lib/auth/PortalBackendProvider";
import { createOrder } from "../../../lib/api/store";
import { createWithdraw, saveWalletAddress } from "../../../lib/api/wallet";
import { createLead, updateLead } from "../../../lib/api/crm";
import { fetchInviteLink, updateProfile } from "../../../lib/api/me";
import { ApiError } from "../../../lib/api/types";
import {
  BINARY_RULES,
  CURRENT_DEMO_TIER,
  PARTNER_RANKS,
  PARTNER_TIERS,
  QUALIFICATION_PERIOD,
  QUICK_START_RULES,
  RANK_QUALIFICATION_RULES,
  SUBSCRIPTION_RULES,
  WITHDRAWAL_RULES,
} from "../../../lib/marketing-plan";
${portalLib}
import { PageShell } from "../shared/PageShell";
import { PortalDialog } from "../shared/PortalDialog";
import { ProgressItem } from "../shared/ProgressItem";
${extraImports}

${exportTopLevel(slice(start, end))}
`,
  );
}

// HomeView + HomeProgramCard (+ HomeProgramItem type)
viewFile("HomeView", 3289, 3757);
// Fix: HomeView file should be 3289-3536 + HomeProgramItem + HomeProgramCard 3706-3757
// ProgressItem is separate. CourseCard goes with CoursesView.
// Re-do HomeView properly:
write(
  "components/portal/views/HomeView.tsx",
  `"use client";

import { useEffect, useRef, useState } from "react";
import type { PointerEvent as ReactPointerEvent } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { AlertTriangle, ArrowUpRight, CheckCircle2, ChevronRight, Play, Rocket, Search, Sparkles } from "lucide-react";
import { usePortalBackend } from "../../../lib/auth/PortalBackendProvider";
import {
  courses,
  extractProgramList,
  mapApiProgramToCourse,
  marketProgramCourseMap,
  marketPrograms,
  promoBanners,
  routeSlug,
} from "../../../lib/portal";
import type { NotifyFn, SectionId, TFn } from "../../../lib/portal";
import { PortalDialog } from "../shared/PortalDialog";

${exportTopLevel(slice(3289, 3536))}

${exportTopLevel(slice(3706, 3757))}
`,
);

write(
  "components/portal/views/CabinetView.tsx",
  `"use client";

import { useEffect, useState } from "react";
import { Check, Trophy, UserPlus } from "lucide-react";
import { useAuth } from "../../../lib/auth/AuthProvider";
import { usePortalBackend } from "../../../lib/auth/PortalBackendProvider";
import { BINARY_RULES, PARTNER_RANKS, QUICK_START_RULES } from "../../../lib/marketing-plan";
import { formatApiDate, formatUsd } from "../../../lib/portal";
import type { NotifyFn, SectionId, TFn } from "../../../lib/portal";
import { PageShell } from "../shared/PageShell";
import { ProgressItem } from "../shared/ProgressItem";
import { PartnersView } from "./PartnersView";

${exportTopLevel(slice(3538, 3684))}
`,
);

write(
  "components/portal/views/CourseCard.tsx",
  `"use client";

import { Play } from "lucide-react";
import { courses } from "../../../lib/portal";
import type { TFn } from "../../../lib/portal";

${exportTopLevel(slice(3759, 3799))}
`,
);

write(
  "components/portal/views/WorkspaceView.tsx",
  `"use client";

import { useState } from "react";
import { Bot, ChevronRight, CircleUserRound, Copy, History, Images, ListChecks, MessageSquareText, Plus, RefreshCw, Save, Send, UserPlus, Video } from "lucide-react";
import type { NotifyFn, TFn } from "../../../lib/portal";
import { PageShell } from "../shared/PageShell";

${exportTopLevel(slice(3801, 3969))}
`,
);

write(
  "components/portal/views/CoursesView.tsx",
  `"use client";

import { useState } from "react";
import { usePortalBackend } from "../../../lib/auth/PortalBackendProvider";
import { courses, extractProgramList, mapApiProgramToCourse } from "../../../lib/portal";
import type { SectionId, TFn } from "../../../lib/portal";
import { PageShell } from "../shared/PageShell";
import { CourseCard } from "./CourseCard";

${exportTopLevel(slice(3971, 3997))}
`,
);

write(
  "components/portal/views/LibraryView.tsx",
  `"use client";

import { useState } from "react";
import { ChevronRight, Search } from "lucide-react";
import { usePortalBackend } from "../../../lib/auth/PortalBackendProvider";
import { formatApiDate, materialCards, materialsFromApi } from "../../../lib/portal";
import type { SectionId, TFn } from "../../../lib/portal";
import { PageShell } from "../shared/PageShell";

${exportTopLevel(slice(3999, 4072))}
`,
);

write(
  "components/portal/views/CourseDetailView.tsx",
  `"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { ArrowUpRight, BookOpen, Check, CheckCircle2, ChevronDown, Grid2X2, Images, ListChecks, Play, ShieldCheck } from "lucide-react";
import { buildCourseCurriculum, courses } from "../../../lib/portal";
import type { NotifyFn, TFn } from "../../../lib/portal";

${exportTopLevel(slice(4177, 4394))}
`,
);

write(
  "components/portal/views/MaterialDetailView.tsx",
  `"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { ChevronRight, Download, Sparkles } from "lucide-react";
import { materialCards } from "../../../lib/portal";
import type { NotifyFn, TFn } from "../../../lib/portal";

${exportTopLevel(slice(4396, 4487))}
`,
);

write(
  "components/portal/views/PartnersView.tsx",
  `"use client";

import { useEffect, useMemo, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { ChevronLeft, ChevronRight, Plus, Send, UserPlus, Workflow } from "lucide-react";
import { CURRENT_DEMO_TIER } from "../../../lib/marketing-plan";
import { TEAM_PARTNER_DIRECTORY } from "../../../lib/portal";
import type { NotifyFn, TFn } from "../../../lib/portal";
import { PageShell } from "../shared/PageShell";
import { PortalDialog } from "../shared/PortalDialog";

${exportTopLevel(slice(4523, 4761))}
`,
);

write(
  "components/portal/views/CrmView.tsx",
  `"use client";

import { useEffect, useRef, useState } from "react";
import { usePathname } from "next/navigation";
import { CalendarDays, History, ListChecks, MessageSquareText, PhoneCall, Plus, Save, Send, X } from "lucide-react";
import { usePortalBackend } from "../../../lib/auth/PortalBackendProvider";
import { createLead, updateLead } from "../../../lib/api/crm";
import { ApiError } from "../../../lib/api/types";
import { createNewCrmLead, crmColumnsForRoute, crmColumnsFromApi, formatCrmPhone } from "../../../lib/portal";
import type { CrmColumn, CrmDeal, CrmTimelineNote, NotifyFn, TFn } from "../../../lib/portal";
import { PageShell } from "../shared/PageShell";

${exportTopLevel(slice(4763, 5100))}
`,
);

write(
  "components/portal/views/MarketplaceView.tsx",
  `"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Check, CheckCircle2, ChevronRight, ShieldCheck, Sparkles, Zap } from "lucide-react";
import { usePortalBackend } from "../../../lib/auth/PortalBackendProvider";
import { createOrder } from "../../../lib/api/store";
import { ApiError } from "../../../lib/api/types";
import { accessPackages, marketOfferFromPathname, marketOfferHref, tokenPacks } from "../../../lib/portal";
import type { MarketOffer, MarketTab, NotifyFn, TFn } from "../../../lib/portal";
import { PageShell } from "../shared/PageShell";
import { PortalDialog } from "../shared/PortalDialog";

${exportTopLevel(slice(5102, 5349))}
`,
);

write(
  "components/portal/views/WalletView.tsx",
  `"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { AlertTriangle, CalendarDays, Check, CheckCircle2, ChevronDown, ClipboardPaste, CreditCard, Filter, History, Info, Search, ShieldCheck, WalletCards } from "lucide-react";
import { usePortalBackend } from "../../../lib/auth/PortalBackendProvider";
import { createWithdraw, saveWalletAddress } from "../../../lib/api/wallet";
import { ApiError } from "../../../lib/api/types";
import { BINARY_RULES, WITHDRAWAL_RULES } from "../../../lib/marketing-plan";
import {
  formatUsd,
  hasUsdtAddress,
  maskWalletAddress,
  PAYOUT_ADDRESS_STORAGE_KEY,
} from "../../../lib/portal";
import type { NotifyFn, TFn, WalletPeriod, WalletTransactionCategory, WalletTransactionType } from "../../../lib/portal";
import { PageShell } from "../shared/PageShell";
import { PortalDialog } from "../shared/PortalDialog";
import { ProgressItem } from "../shared/ProgressItem";

${exportTopLevel(slice(5358, 5798))}
`,
);

write(
  "components/portal/views/ProfileView.tsx",
  `"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { AlertTriangle, Bell, Camera, Check, CheckCircle2, ChevronRight, CircleUserRound, ClipboardPaste, Copy, CreditCard, History, Lock, MapPin, Settings, ShieldCheck, ShoppingBag, Smartphone, UserPlus, Users, WalletCards } from "lucide-react";
import { useAuth } from "../../../lib/auth/AuthProvider";
import { usePortalBackend } from "../../../lib/auth/PortalBackendProvider";
import { fetchInviteLink, updateProfile } from "../../../lib/api/me";
import { ApiError } from "../../../lib/api/types";
import { CURRENT_DEMO_TIER, SUBSCRIPTION_RULES } from "../../../lib/marketing-plan";
import { hasUsdtAddress, maskWalletAddress, PAYOUT_ADDRESS_STORAGE_KEY } from "../../../lib/portal";
import type { NotifyFn, SectionId, TFn } from "../../../lib/portal";
import { PageShell } from "../shared/PageShell";
import { PortalDialog } from "../shared/PortalDialog";

${exportTopLevel(slice(5800, 6157))}
`,
);

write(
  "components/portal/views/LaborMarketView.tsx",
  `"use client";

import { useState } from "react";
import { ChevronRight, History, MapPin, Plus, Search, ShieldCheck } from "lucide-react";
import type { NotifyFn, TFn } from "../../../lib/portal";
import { PageShell } from "../shared/PageShell";

${exportTopLevel(slice(6159, 6308))}
`,
);

write(
  "components/portal/views/ChatsView.tsx",
  `"use client";

import { ArrowUpRight, ExternalLink, Headphones, Megaphone, MessageSquareText, Rocket, ShieldCheck, Sparkles, UserPlus, Users } from "lucide-react";
import { openTelegramResource } from "../../../lib/portal";
import type { NotifyFn, TelegramResourceId, TFn } from "../../../lib/portal";
import { PageShell } from "../shared/PageShell";

${exportTopLevel(slice(6310, 6384))}
`,
);

console.log("views done");
