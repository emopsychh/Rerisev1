/**
 * Phase 3: PortalApp + PortalShell + thin page.tsx
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
  return code.replace(/^function /gm, "export function ");
}

function write(rel, content) {
  const full = path.join(ROOT, rel);
  fs.mkdirSync(path.dirname(full), { recursive: true });
  const out = content.replace(/\n+$/, "") + "\n";
  fs.writeFileSync(full, out, "utf8");
  console.log("wrote", rel, "(" + out.split("\n").length + " lines)");
}

write(
  "components/portal/PortalShell.tsx",
  `"use client";

import {
  Bell,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Grid2X2,
  Headphones,
  Lock,
  UserPlus,
  Users,
  X,
} from "lucide-react";
import { ThemeToggle } from "../../app/theme-toggle";
import { usePortalBackend } from "../../lib/auth/PortalBackendProvider";
import { CURRENT_DEMO_TIER } from "../../lib/marketing-plan";
import {
  courses,
  formatApiDate,
  languages,
  materialCards,
  mobileLabels,
  mobileMoreIds,
  mobileNavIds,
  navItems,
  tariffDisplayName,
} from "../../lib/portal";
import type { DetailView, Lang, MarketTab, NotifyFn, SectionId, TFn } from "../../lib/portal";
import type { MeUser } from "../../lib/api/types";
import { InviteDialog } from "./dialogs/InviteDialog";
import { RenewalDialog } from "./dialogs/RenewalDialog";
import { StatusLadderDialog } from "./dialogs/StatusLadderDialog";
import { CabinetView } from "./views/CabinetView";
import { ChatsView } from "./views/ChatsView";
import { CourseDetailView } from "./views/CourseDetailView";
import { CoursesView } from "./views/CoursesView";
import { CrmView } from "./views/CrmView";
import { HomeView } from "./views/HomeView";
import { LaborMarketView } from "./views/LaborMarketView";
import { LibraryView } from "./views/LibraryView";
import { MarketplaceView } from "./views/MarketplaceView";
import { MaterialDetailView } from "./views/MaterialDetailView";
import { PartnersView } from "./views/PartnersView";
import { ProfileView } from "./views/ProfileView";
import { WalletView } from "./views/WalletView";
import { WorkspaceView } from "./views/WorkspaceView";

${exportTopLevel(slice(2962, 3268))}
`,
);

write(
  "components/portal/PortalApp.tsx",
  `"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "../../lib/auth/AuthProvider";
import { PortalBackendProvider } from "../../lib/auth/PortalBackendProvider";
import {
  courses,
  materialCards,
  marketTabFromPathname,
  matchesRoute,
  pageTitle,
  routeSlug,
  sectionFromPathname,
  sectionHref,
  sectionIds,
  translate,
} from "../../lib/portal";
import type { DetailView, Lang, MarketTab, NotifyFn, SectionId, TFn } from "../../lib/portal";
import { PortalShellInner } from "./PortalShell";

${exportTopLevel(slice(2703, 2960))}
`,
);

write(
  "app/page.tsx",
  `"use client";

import { Suspense } from "react";
import { PortalAppContent } from "../components/portal/PortalApp";

export default function HomePage() {
  return (
    <Suspense fallback={null}>
      <PortalAppContent />
    </Suspense>
  );
}
`,
);

console.log("phase3 done");
