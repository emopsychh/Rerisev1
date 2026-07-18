"use client";

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
import { useAuth } from "../../lib/auth/AuthProvider";
import { usePortalBackend } from "../../lib/auth/PortalBackendProvider";
import { markAllNotificationsRead, markNotificationRead } from "../../lib/api/me";
import {
  formatApiDate,
  formatLeadTime,
  materialsFromApi,
  mobileLabels,
  mobileMoreIds,
  mobileNavIds,
  navItems,
  tariffDisplayName,
} from "../../lib/portal";
import type { DetailView, MarketTab, NotifyFn, SectionId, TFn } from "../../lib/portal";
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

function notificationTarget(type: string): SectionId {
  if (type === "bonus") return "wallet";
  if (type === "crm") return "crm";
  if (type === "access") return "marketplace";
  return "home";
}

export function PortalShellInner(props: {
  active: SectionId;
  detail: DetailView | null;
  t: TFn;
  title: string;
  marketTab: MarketTab;
  goSection: (id: SectionId) => void;
  goMarketTab: (tab: MarketTab) => void;
  goHomeFromBrand: () => void;
  goBack: () => void;
  openCourse: (courseSlug: string, returnTo: SectionId, courseTitle?: string) => void;
  openMaterial: (groupId: number, materialTitle: string) => void;
  openInvite: () => void;
  openRenewal: () => void;
  openRanks: () => void;
  openAiHub: () => void;
  closeInvite: () => void;
  closePortalDialog: () => void;
  notify: NotifyFn;
  toast: string | null;
  isInviteOpen: boolean;
  isRenewalOpen: boolean;
  isRanksOpen: boolean;
  isMobileMoreOpen: boolean;
  setIsMobileMoreOpen: (v: boolean) => void;
  isNotificationsOpen: boolean;
  setIsNotificationsOpen: (v: boolean | ((v: boolean) => boolean)) => void;
  notificationCount: number;
  setNotificationCount: (v: number | ((n: number) => number)) => void;
  logout: () => void;
  user: { first_name: string; last_name: string; email: string; public_id: string };
}) {
  const {
    active, detail, t, title, marketTab, goSection, goMarketTab, goHomeFromBrand, goBack,
    openCourse, openMaterial, openInvite, openRenewal, openRanks, openAiHub,
    closeInvite, closePortalDialog, notify, toast,
    isInviteOpen, isRenewalOpen, isRanksOpen, isMobileMoreOpen, setIsMobileMoreOpen,
    isNotificationsOpen, setIsNotificationsOpen, notificationCount, setNotificationCount,
    logout, user,
  } = props;
  const { refreshMe } = useAuth();
  const backend = usePortalBackend();
  const materialCatalog = materialsFromApi(backend.materials)?.items ?? [];
  const partnerSummary = backend.home?.partner_summary;
  const hasTariff = Boolean(partnerSummary?.tariff_id);
  const sidebarTariffName = hasTariff
    ? tariffDisplayName(partnerSummary!.tariff_id)
    : t("Не оформлен");
  const activityUntilRaw = (backend.dashboard?.partner as { activity_until?: unknown } | undefined)?.activity_until;
  const sidebarActiveUntil = hasTariff && activityUntilRaw
    ? formatApiDate(activityUntilRaw, "—")
    : null;
  const canRenew = Boolean(partnerSummary?.can_renew);
  const liveNotifications = backend.notifications.slice(0, 8).map((item) => {
    const type = String(item.type || "system");
    const body = String(item.body || "").trim();
    const when = formatLeadTime(item.created_at);
    return {
      id: Number(item.id),
      label: String(item.title || "Уведомление"),
      meta: body ? `${body} · ${when}` : when,
      target: notificationTarget(type),
      isRead: Boolean(item.is_read),
    };
  });
  const markAllRead = async () => {
    try {
      await markAllNotificationsRead();
      setNotificationCount(0);
      await Promise.all([backend.reload(), refreshMe()]);
    } catch {
      notify(t("Не удалось отметить уведомления"));
    }
  };
  const openNotification = async (item: (typeof liveNotifications)[number]) => {
    setIsNotificationsOpen(false);
    if (!item.isRead && item.id) {
      try {
        await markNotificationRead(item.id);
        setNotificationCount((count) => Math.max(0, count - 1));
        await Promise.all([backend.reload(), refreshMe()]);
      } catch {
        /* navigation still proceeds */
      }
    }
    goSection(item.target);
  };
  const teamSummary = (backend.structure as { summary?: { total_members?: number; active_members?: number } } | null)?.summary;

  return (
    <main className="portal-shell">
      <aside className="portal-sidebar">
        <button type="button" className="brand" onClick={goHomeFromBrand} aria-label={t("Перейти на главную страницу")}>
          <div className="brand-cube">
            <span>R</span>
          </div>
          <div>
            <strong>RE<span className="brand-separator">:</span>RISE</strong>
            <small>{user.public_id || "Digital Network"}</small>
          </div>
        </button>

        <nav className="side-nav" aria-label={t("Главная навигация")}>
          {navItems.filter((item) => item.id !== "workspace").map((item) => {
            const isActive = item.id === "home"
              ? active === "home" || active === "courses"
              : active === item.id;
            return (
              <button
                className={isActive ? "side-link active" : "side-link"}
                key={item.id}
                onClick={() => item.id === "marketplace" ? goMarketTab("packages") : goSection(item.id)}
              >
                <item.icon size={22} />
                <span>{t(item.label)}</span>
              </button>
            );
          })}
        </nav>
        <button type="button" className="side-link logout-link" onClick={() => { logout(); window.location.href = "/login"; }}>
          <Lock size={22} />
          <span>{t("Выйти")}</span>
        </button>

        <div className="sidebar-bottom">
          <div className={`sidebar-card pro-card${hasTariff ? "" : " idle"}`}>
            <small>{t("Тариф")}</small>
            <span>{sidebarTariffName}</span>
            <p>
              {hasTariff
                ? (sidebarActiveUntil ? `${t("Активность")} · ${t("до")} ${sidebarActiveUntil}` : t("Активность не указана"))
                : t("Подписка ещё не оформлена")}
            </p>
            {hasTariff && canRenew ? (
              <button type="button" onClick={openRenewal}>
                {t("Продлить")}
                <ChevronRight size={16} />
              </button>
            ) : !hasTariff ? (
              <button type="button" onClick={() => goMarketTab("packages")}>
                {t("Выбрать тариф")}
                <ChevronRight size={16} />
              </button>
            ) : (
              <button type="button" onClick={() => goSection("marketplace")}>
                {t("Маркет")}
                <ChevronRight size={16} />
              </button>
            )}
          </div>

          <button type="button" className="support-button" onClick={() => notify(t("Чат поддержки открыт"))}>
            <Headphones size={20} />
            <span>{t("Поддержка")}</span>
          </button>
        </div>
      </aside>

      <section className={active === "crm" && !detail ? "portal-main crm-main" : "portal-main"}>
        <header className="portal-topbar">
          <div className="topbar-title">
            {detail ? (
              <button className="topbar-back" onClick={goBack} aria-label={t("Назад")}>
                <ChevronLeft size={20} />
              </button>
            ) : null}
            {!detail && active === "partners" ? (
              <div className="topbar-team-title">
                <h1>{title}</h1>
                <div className="topbar-team-metrics" aria-label={t("Общие показатели команды")}>
                  <span><Users size={15} /><strong>{teamSummary?.total_members ?? 0}</strong><small>{t("партнёров")}</small></span>
                  <span><i /><strong>{teamSummary?.active_members ?? 0}</strong><small>{t("активных")}</small></span>
                </div>
              </div>
            ) : <h1>{title}</h1>}
            {!detail && active === "marketplace" ? (
              <div className="topbar-section-switch" aria-label={t("Разделы маркета")}>
                <button className={marketTab === "packages" ? "active" : ""} onClick={() => {
                  goMarketTab("packages");
                }} type="button">
                  <span>{t("Тарифы")}</span>
                </button>
                <button className={marketTab === "tokens" ? "active" : ""} onClick={() => {
                  goMarketTab("tokens");
                }} type="button">
                  <span>{t("Токены")}</span>
                </button>
              </div>
            ) : null}
          </div>

          <div className="topbar-actions">
            <button className="invite-button" onClick={openInvite}>
              <UserPlus size={18} />
              {t("Пригласить")}
            </button>
            <ThemeToggle className="topbar-theme-toggle" />
            <button
              className="bell-button"
              aria-label={t("Уведомления")}
              aria-expanded={isNotificationsOpen}
              onClick={() => setIsNotificationsOpen((isOpen) => !isOpen)}
            >
              <Bell size={20} />
              {notificationCount > 0 ? <i>{notificationCount}</i> : null}
            </button>
            {isNotificationsOpen ? (
              <div className="notification-popover">
                <div>
                  <strong>{t("Уведомления")}</strong>
                  {liveNotifications.length > 0 ? (
                    <button type="button" onClick={() => void markAllRead()}>{t("Прочитать все")}</button>
                  ) : null}
                </div>
                {liveNotifications.length === 0 ? (
                  <p className="notification-popover-empty">{t("Пока нет уведомлений")}</p>
                ) : (
                  liveNotifications.map((item) => (
                    <button
                      key={item.id || item.label}
                      type="button"
                      className={item.isRead ? "is-read" : undefined}
                      onClick={() => void openNotification(item)}
                    >
                      <span />
                      <div>
                        <strong>{item.label}</strong>
                        <small>{item.meta}</small>
                      </div>
                    </button>
                  ))
                )}
              </div>
            ) : null}
          </div>
        </header>

        {detail?.type === "course" ? <CourseDetailView slug={detail.slug} t={t} notify={notify} /> : null}
        {detail?.type === "material" ? (
          <MaterialDetailView
            material={
              materialCatalog.find((item) => item.id === detail.groupId) ?? {
                id: detail.groupId,
                title: detail.title,
                text: "",
                count: 0,
                updated: "—",
                category: t("Материалы"),
                color: "blue",
              }
            }
            t={t}
            notify={notify}
            openAiHub={openAiHub}
          />
        ) : null}
        {!detail && active === "home" ? <HomeView setActive={goSection} openCourse={openCourse} openAiHub={openAiHub} t={t} notify={notify} /> : null}
        {!detail && active === "cabinet" ? <CabinetView setActive={goSection} t={t} notify={notify} onInvite={openInvite} onOpenRanks={openRanks} /> : null}
        {!detail && active === "workspace" ? <WorkspaceView t={t} notify={notify} /> : null}
        {!detail && active === "courses" ? <CoursesView openCourse={openCourse} t={t} /> : null}
        {!detail && active === "library" ? <LibraryView openMaterial={openMaterial} t={t} /> : null}
        {!detail && active === "labor" ? <LaborMarketView t={t} notify={notify} /> : null}
        {!detail && active === "chats" ? <ChatsView t={t} notify={notify} /> : null}
        {!detail && active === "partners" ? <PartnersView t={t} notify={notify} /> : null}
        {!detail && active === "crm" ? <CrmView t={t} notify={notify} /> : null}
        {!detail && active === "marketplace" ? <MarketplaceView t={t} notify={notify} marketTab={marketTab} /> : null}
        {!detail && active === "wallet" ? <WalletView t={t} notify={notify} /> : null}
        {!detail && active === "profile" ? <ProfileView t={t} notify={notify} setActive={goSection} onRenew={openRenewal} /> : null}
      </section>

      <nav className="mobile-nav" aria-label={t("Мобильная навигация")}>
        {mobileNavIds.map((id) => navItems.find((item) => item.id === id)!).map((item) => (
          <button
            type="button"
            className={active === item.id || (item.id === "home" && active === "courses") ? "mobile-link active" : "mobile-link"}
            key={item.id}
            onClick={() => item.id === "workspace" ? openAiHub() : item.id === "marketplace" ? goMarketTab("packages") : goSection(item.id)}
          >
            <item.icon size={20} />
            <span>{t(mobileLabels[item.id])}</span>
          </button>
        ))}
        <button
          type="button"
          className={mobileMoreIds.includes(active) ? "mobile-link active" : "mobile-link"}
          onClick={() => setIsMobileMoreOpen(true)}
        >
          <Grid2X2 size={20} />
          <span>{t("Ещё")}</span>
        </button>
      </nav>

      {isMobileMoreOpen ? (
        <div className="mobile-more-backdrop" onClick={() => setIsMobileMoreOpen(false)}>
          <section
            className="mobile-more-sheet"
            role="dialog"
            aria-modal="true"
            aria-label={t("Вся платформа")}
            onClick={(event) => event.stopPropagation()}
          >
            <header>
              <div>
                <span>{t("Разделы RE:RISE")}</span>
                <h2>{t("Вся платформа")}</h2>
              </div>
              <button type="button" onClick={() => setIsMobileMoreOpen(false)} aria-label={t("Закрыть")}><X size={20} /></button>
            </header>
            <div>
              {mobileMoreIds.map((id) => navItems.find((item) => item.id === id)!).map((item) => (
                <button type="button" key={item.id} onClick={() => goSection(item.id)}>
                  <item.icon size={21} />
                  <span>{t(item.label)}</span>
                  <ChevronRight size={18} />
                </button>
              ))}
            </div>
            <footer className="mobile-theme-footer">
              <ThemeToggle className="mobile-theme-toggle" />
            </footer>
          </section>
        </div>
      ) : null}

      {isInviteOpen ? <InviteDialog onClose={closeInvite} notify={notify} t={t} /> : null}
      {isRenewalOpen ? <RenewalDialog onClose={closePortalDialog} notify={notify} t={t} /> : null}
      {isRanksOpen ? <StatusLadderDialog onClose={closePortalDialog} t={t} /> : null}
      {toast ? (
        <div className="portal-toast" role="status">
          <CheckCircle2 size={19} />
          <span>{toast}</span>
        </div>
      ) : null}
    </main>
  );
}
