"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "../../lib/auth/AuthProvider";
import { usePortalBackend } from "../../lib/auth/PortalBackendProvider";
import {
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
import { PortalLoading } from "./shared/PortalLoading";
import { PortalShellInner } from "./PortalShell";

export function PortalAppContent() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { user, loading: authLoading, logout } = useAuth();
  const { ready: backendReady } = usePortalBackend();
  const [active, setActive] = useState<SectionId>(() => {
    if (pathname === "/") {
      const requestedSection = searchParams.get("section");
      return requestedSection && sectionIds.has(requestedSection as SectionId) ? requestedSection as SectionId : "home";
    }
    const routedSection = sectionFromPathname(pathname);
    if (routedSection) return routedSection;
    return "home";
  });
  const [detail, setDetail] = useState<DetailView | null>(null);
  const [lang, setLang] = useState<Lang>("ru");
  const [isLangOpen, setIsLangOpen] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const [isInviteOpen, setIsInviteOpen] = useState(false);
  const [isRenewalOpen, setIsRenewalOpen] = useState(false);
  const [isRanksOpen, setIsRanksOpen] = useState(false);
  const [isMobileMoreOpen, setIsMobileMoreOpen] = useState(false);
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);
  const [notificationCount, setNotificationCount] = useState(3);
  const [marketTab, setMarketTab] = useState<MarketTab>(() => marketTabFromPathname(pathname) ?? "packages");
  const languageSwitcherRef = useRef<HTMLDivElement | null>(null);
  const t = useMemo<TFn>(() => (value: string) => translate(value, lang), [lang]);
  const title = useMemo(
    () => (detail ? t(detail.type === "course" ? (detail.title || detail.slug) : detail.title) : pageTitle(active, t)),
    [active, detail, t],
  );
  const openCourse = (courseSlug: string, returnTo: SectionId, courseTitle?: string) => {
    setDetail({ type: "course", slug: courseSlug, title: courseTitle, returnTo });
    router.push(`/courses/${courseSlug}?from=${returnTo}`, { scroll: false });
  };
  const openMaterial = (materialTitle: string) => {
    setDetail({ type: "material", title: materialTitle, returnTo: "library" });
    router.push(`/materials/${routeSlug(materialTitle)}`, { scroll: false });
  };
  const openInvite = () => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("dialog", "invite");
    setIsInviteOpen(true);
    router.push(`${pathname}?${params.toString()}`, { scroll: false });
  };
  const closeInvite = () => {
    const params = new URLSearchParams(searchParams.toString());
    params.delete("dialog");
    const nextQuery = params.toString();
    setIsInviteOpen(false);
    router.replace(`${pathname}${nextQuery ? `?${nextQuery}` : ""}`, { scroll: false });
  };
  const openRenewal = () => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("dialog", "renew");
    setIsRenewalOpen(true);
    router.push(`${pathname}?${params.toString()}`, { scroll: false });
  };
  const openRanks = () => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("dialog", "statuses");
    setIsRanksOpen(true);
    router.push(`${pathname}?${params.toString()}`, { scroll: false });
  };
  const closePortalDialog = () => {
    const params = new URLSearchParams(searchParams.toString());
    params.delete("dialog");
    const nextQuery = params.toString();
    setIsRenewalOpen(false);
    setIsRanksOpen(false);
    router.replace(`${pathname}${nextQuery ? `?${nextQuery}` : ""}`, { scroll: false });
  };
  const notify: NotifyFn = (message) => setToast(message);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      router.replace("/login");
    }
  }, [authLoading, user, router]);

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "auto" });
  }, [active, detail]);

  useEffect(() => {
    if (matchesRoute(pathname, "/marketing")) {
      setActive("chats");
      setDetail(null);
      router.replace("/chats", { scroll: false });
      return;
    }

    if (pathname === "/market" || pathname === "/market/programs") {
      setActive("marketplace");
      setMarketTab("packages");
      setDetail(null);
      router.replace("/market/packages", { scroll: false });
      return;
    }

    const courseMatch = pathname.match(/^\/courses\/([^/]+)/);
    if (courseMatch?.[1]) {
      const courseSlug = courseMatch[1];
      const requestedParent = searchParams.get("from");
      const returnTo = requestedParent && sectionIds.has(requestedParent as SectionId) ? requestedParent as SectionId : "courses";
      setActive(returnTo);
      setDetail((currentDetail) => currentDetail?.type === "course" && currentDetail.slug === courseSlug && currentDetail.returnTo === returnTo
        ? currentDetail
        : { type: "course", slug: courseSlug, returnTo });
      return;
    }

    const materialMatch = pathname.match(/^\/materials\/([^/]+)/);
    const material = materialMatch ? materialCards.find((item) => routeSlug(item.title) === materialMatch[1]) : null;
    if (material) {
      setActive("library");
      setDetail({ type: "material", title: material.title, returnTo: "library" });
      return;
    }

    if (pathname === "/") {
      const requestedSection = searchParams.get("section");
      setActive(requestedSection && sectionIds.has(requestedSection as SectionId) ? requestedSection as SectionId : "home");
      setDetail(null);
      return;
    }

    const routedSection = sectionFromPathname(pathname);
    if (routedSection) {
      setActive(routedSection);
      setDetail(null);
      const routedMarketTab = marketTabFromPathname(pathname);
      if (routedMarketTab) setMarketTab(routedMarketTab);
    }
  }, [pathname, searchParams]);

  useEffect(() => {
    setIsInviteOpen(searchParams.get("dialog") === "invite");
    setIsRenewalOpen(searchParams.get("dialog") === "renew");
    setIsRanksOpen(searchParams.get("dialog") === "statuses");
  }, [searchParams]);

  useEffect(() => {
    if (!toast) return;
    const timer = window.setTimeout(() => setToast(null), 2600);
    return () => window.clearTimeout(timer);
  }, [toast]);

  useEffect(() => {
    if (!isLangOpen) return;

    const closeOnOutsidePress = (event: PointerEvent) => {
      if (event.target instanceof Node && !languageSwitcherRef.current?.contains(event.target)) {
        setIsLangOpen(false);
      }
    };
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setIsLangOpen(false);
      }
    };

    document.addEventListener("pointerdown", closeOnOutsidePress);
    document.addEventListener("keydown", closeOnEscape);

    return () => {
      document.removeEventListener("pointerdown", closeOnOutsidePress);
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, [isLangOpen]);

  const goSection = (section: SectionId) => {
    setDetail(null);
    setActive(section);
    setIsMobileMoreOpen(false);
    setIsNotificationsOpen(false);
    setIsLangOpen(false);
    router.push(sectionHref(section), { scroll: false });
  };
  const goMarketTab = (tab: MarketTab) => {
    setDetail(null);
    setActive("marketplace");
    setMarketTab(tab);
    setIsMobileMoreOpen(false);
    setIsNotificationsOpen(false);
    setIsLangOpen(false);
    router.push(`/market/${tab}`, { scroll: false });
  };
  const goHomeFromBrand = () => {
    setDetail(null);
    setActive("home");
    setIsMobileMoreOpen(false);
    setIsNotificationsOpen(false);
    setIsLangOpen(false);
    setIsInviteOpen(false);
    setIsRenewalOpen(false);
    setIsRanksOpen(false);
    router.push("/", { scroll: true });
    window.requestAnimationFrame(() => window.scrollTo({ top: 0, behavior: "auto" }));
  };
  const goBack = () => {
    if (!detail) return;
    setActive(detail.returnTo);
    setDetail(null);
    router.push(sectionHref(detail.returnTo), { scroll: false });
  };
  const openAiBox = () => {
    setActive("workspace");
    router.push("/?section=workspace", { scroll: false });
  };

  if (authLoading || !user) {
    return <main className="auth-shell"><p className="auth-loading">Загрузка…</p></main>;
  }

  // Не размонтируем shell при подгрузке данных — иначе вспышка «Загрузка портала…».
  if (!backendReady) {
    return (
      <main className="auth-shell">
        <PortalLoading label={t("Загрузка портала…")} />
      </main>
    );
  }

  return (
    <PortalShellInner
      active={active}
      detail={detail}
      t={t}
      title={title}
      marketTab={marketTab}
      goSection={goSection}
      goMarketTab={goMarketTab}
      goHomeFromBrand={goHomeFromBrand}
      goBack={goBack}
      openCourse={openCourse}
      openMaterial={openMaterial}
      openInvite={openInvite}
      openRenewal={openRenewal}
      openRanks={openRanks}
      openAiBox={openAiBox}
      closeInvite={closeInvite}
      closePortalDialog={closePortalDialog}
      notify={notify}
      toast={toast}
      isInviteOpen={isInviteOpen}
      isRenewalOpen={isRenewalOpen}
      isRanksOpen={isRanksOpen}
      isMobileMoreOpen={isMobileMoreOpen}
      setIsMobileMoreOpen={setIsMobileMoreOpen}
      isNotificationsOpen={isNotificationsOpen}
      setIsNotificationsOpen={setIsNotificationsOpen}
      notificationCount={user.unread_notifications ?? notificationCount}
      setNotificationCount={setNotificationCount}
      lang={lang}
      setLang={setLang}
      isLangOpen={isLangOpen}
      setIsLangOpen={setIsLangOpen}
      languageSwitcherRef={languageSwitcherRef}
      logout={logout}
      user={user}
    />
  );
}
