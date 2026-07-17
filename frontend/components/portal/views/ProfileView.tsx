"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { AlertTriangle, Bell, Camera, Check, CheckCircle2, ChevronRight, CircleUserRound, ClipboardPaste, Copy, CreditCard, History, Lock, MapPin, Settings, ShieldCheck, ShoppingBag, Smartphone, UserPlus, Users, WalletCards } from "lucide-react";
import { useAuth } from "../../../lib/auth/AuthProvider";
import { usePortalBackend } from "../../../lib/auth/PortalBackendProvider";
import { fetchInviteLink, fetchProfile, updateProfile } from "../../../lib/api/me";
import { ApiError } from "../../../lib/api/types";
import { CURRENT_DEMO_TIER, PARTNER_RANKS, SUBSCRIPTION_RULES } from "../../../lib/marketing-plan";
import { formatApiDate, maskWalletAddress, PAYOUT_ADDRESS_STORAGE_KEY, tariffDisplayName } from "../../../lib/portal";
import type { NotifyFn, SectionId, TFn } from "../../../lib/portal";
import { PageShell } from "../shared/PageShell";
import { PortalDialog } from "../shared/PortalDialog";
import { PortalLoading } from "../shared/PortalLoading";

export function ProfileView({ t, notify, setActive, onRenew }: { t: TFn; notify: NotifyFn; setActive: (id: SectionId) => void; onRenew: () => void }) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, refreshMe } = useAuth();
  const { wallet, home, dashboard, ready } = usePortalBackend();
  const partnerFromHome = home?.partner_summary;
  const partnerFromDash = dashboard?.partner as {
    tariff_id?: string;
    tariff_name?: string;
    is_active?: boolean;
    activity_until?: string;
    current_rank_name?: string;
  } | undefined;
  const tariffLabel = partnerFromDash?.tariff_name
    || (partnerFromHome?.tariff_id || partnerFromDash?.tariff_id
      ? tariffDisplayName(partnerFromHome?.tariff_id || partnerFromDash?.tariff_id)
      : t("Не оформлен"));
  const rankLabel = partnerFromDash?.current_rank_name || partnerFromHome?.current_rank_name || PARTNER_RANKS[0].name;
  const activityUntil = formatApiDate(partnerFromDash?.activity_until, "—");
  const isActive = partnerFromHome?.is_active ?? partnerFromDash?.is_active ?? false;
  const [inviteUrl, setInviteUrl] = useState(user?.public_id ? `rerise.app/join/${user.public_id}` : "rerise.app");
  const [profileData, setProfileData] = useState({
    name: user?.first_name || "",
    surname: user?.last_name || "",
    phone: user?.phone || "",
    email: user?.email || "",
    country: "Россия",
    city: "",
    language: user?.language === "en" ? "English" : user?.language === "es" ? "Español" : "Русский",
  });
  const initials = `${(profileData.name || user?.first_name || "?").slice(0, 1)}${(profileData.surname || user?.last_name || "").slice(0, 1)}`.toUpperCase();
  const [profileDraft, setProfileDraft] = useState(profileData);
  const [profilePayoutAddress, setProfilePayoutAddress] = useState("");
  const [profilePayoutAddressDraft, setProfilePayoutAddressDraft] = useState("");
  const profileDialogFromPath = pathname.match(/^\/profile\/(data|security|wallet)$/);
  const [profileDialog, setProfileDialog] = useState<"data" | "security" | "wallet" | null>(() => (
    profileDialogFromPath?.[1] as "data" | "security" | "wallet" | undefined
  ) ?? null);
  const [avatarUpdated, setAvatarUpdated] = useState(false);
  const [notificationSettings, setNotificationSettings] = useState({ email: true, push: false });
  const profileFields = [
    ["Имя", profileData.name],
    ["Фамилия", profileData.surname],
    ["Телефон", profileData.phone],
    ["Email", profileData.email],
    ["Страна", profileData.country],
    ["Город", profileData.city],
    ["Язык интерфейса", profileData.language],
  ];
  const openProfileDialog = (dialog: "data" | "security" | "wallet") => {
    if (dialog === "wallet") setProfilePayoutAddressDraft(profilePayoutAddress);
    setProfileDialog(dialog);
    router.push(`/profile/${dialog}`, { scroll: false });
  };
  const closeProfileDialog = () => {
    setProfileDialog(null);
    router.push("/profile", { scroll: false });
  };

  useEffect(() => {
    if (!user) return;
    const next = {
      name: user.first_name || "",
      surname: user.last_name || "",
      phone: user.phone || "",
      email: user.email || "",
      country: "Россия",
      city: "",
      language: user.language === "en" ? "English" : user.language === "es" ? "Español" : "Русский",
    };
    setProfileData(next);
    setProfileDraft(next);
    void (async () => {
      try {
        const profile = await fetchProfile();
        const enriched = {
          name: profile.first_name || next.name,
          surname: profile.last_name || next.surname,
          phone: profile.phone || next.phone,
          email: profile.email || next.email,
          country: profile.country || next.country,
          city: profile.city || next.city,
          language: profile.language === "en" ? "English" : profile.language === "es" ? "Español" : "Русский",
        };
        setProfileData(enriched);
        setProfileDraft(enriched);
      } catch {
        /* keep /me values */
      }
      try {
        const invite = await fetchInviteLink();
        if (invite.invite_url) setInviteUrl(invite.invite_url);
      } catch {
        setInviteUrl(user.public_id ? `rerise.app/join/${user.public_id}` : "rerise.app");
      }
    })();
  }, [user]);

  useEffect(() => {
    const dialogMatch = pathname.match(/^\/profile\/(data|security|wallet)$/);
    setProfileDialog((dialogMatch?.[1] as "data" | "security" | "wallet" | undefined) ?? null);
  }, [pathname]);

  useEffect(() => {
    const savedAddress =
      (wallet?.saved_address as { address?: string } | null)?.address ||
      window.localStorage.getItem(PAYOUT_ADDRESS_STORAGE_KEY) ||
      "";
    setProfilePayoutAddress(savedAddress);
    setProfilePayoutAddressDraft(savedAddress);
  }, [wallet]);

  const copyReferral = async () => {
    try {
      const data = await fetchInviteLink();
      if (data.invite_url) setInviteUrl(data.invite_url);
      await navigator.clipboard.writeText(data.invite_url || inviteUrl);
    } catch {
      await navigator.clipboard.writeText(inviteUrl);
    } finally {
      notify(t("Ссылка скопирована"));
    }
  };

  if (!ready) {
    return (
      <PageShell>
        <PortalLoading label={t("Загрузка профиля…")} />
      </PageShell>
    );
  }

  return (
    <PageShell>
      <section className="profile-page">
        <article className="profile-surface">
          <header className="profile-overview">
            <div className="profile-overview-main">
              <span className="profile-avatar-wrap">
                <span className={avatarUpdated ? "avatar-photo big updated" : "avatar-photo big"}>{avatarUpdated ? <Check size={24} /> : initials}</span>
                <i aria-hidden="true" />
              </span>
              <div className="profile-overview-copy">
                <small>{t("Профиль партнера")}</small>
                <h2>{profileData.name} {profileData.surname}</h2>
                <div className="profile-meta-line">
                  <span>{user?.public_id || "—"}</span>
                  <span>{tariffLabel}</span>
                  <span>{isActive ? t("Активна") : t("Неактивна")}</span>
                </div>
              </div>
            </div>
            <div className="profile-header-actions">
              <button onClick={() => {
                setAvatarUpdated((updated) => !updated);
                notify(t("Фото профиля обновлено"));
              }}><Camera size={17} />{t("Сменить фото")}</button>
              <button onClick={() => {
                setProfileDraft(profileData);
                openProfileDialog("data");
              }}><Settings size={17} />{t("Изменить профиль")}</button>
            </div>
          </header>

          <div className="profile-summary-strip" aria-label={t("Партнёрский профиль")}>
            {[
              [ShieldCheck, "Статус", rankLabel],
              [CreditCard, "Тариф", tariffLabel],
              [CheckCircle2, "Активность", `${t("до")} ${activityUntil}`],
              [MapPin, "Регион", profileData.city || profileData.country || "—"],
            ].map(([SummaryIcon, label, value]) => {
              const Icon = SummaryIcon as typeof ShieldCheck;
              return (
                <div className="profile-summary-item" key={label as string}>
                  <Icon size={17} />
                  <span>{t(label as string)}</span>
                  <strong>{t(value as string)}</strong>
                </div>
              );
            })}
          </div>

          <div className="profile-content-grid">
            <div className="profile-main-column">
              <section className="profile-section profile-data-section">
                <div className="profile-section-head">
                  <div className="profile-section-title">
                    <span><CircleUserRound size={19} /></span>
                    <div><small>{t("Профиль")}</small><h3>{t("Личные данные")}</h3></div>
                  </div>
                  <button onClick={() => {
                    setProfileDraft(profileData);
                    openProfileDialog("data");
                  }}>{t("Изменить")}</button>
                </div>
                <div className="profile-field-grid">
                  {profileFields.map(([label, value]) => (
                    <div className="profile-field" key={label}>
                      <span>{t(label)}</span>
                      <strong>{t(value)}</strong>
                    </div>
                  ))}
                </div>
              </section>

              <section className="profile-section profile-partner-section">
                <div className="profile-section-head">
                  <div className="profile-section-title">
                    <span><UserPlus size={19} /></span>
                    <div><small>{t("Партнёрский профиль")}</small><h3>{t("Партнерские настройки")}</h3></div>
                  </div>
                </div>
                <div className="profile-referral-row">
                  <span><Copy size={18} /></span>
                  <div><small>{t("Реферальная ссылка")}</small><strong>{inviteUrl}</strong></div>
                  <button onClick={copyReferral}>{t("Скопировать")}</button>
                </div>
                <div className="profile-setting-grid">
                  <div className="profile-setting-item">
                    <span><Users size={18} /></span>
                    <div><small>{t("Публичный ID")}</small><strong>{user?.public_id || "—"}</strong></div>
                  </div>
                  <div className="profile-setting-item">
                    <span><WalletCards size={18} /></span>
                    <div><small>{t("Кошелек выплат")}</small><strong>{profilePayoutAddress ? `USDT · ${maskWalletAddress(profilePayoutAddress)}` : t("Адрес не указан")}</strong></div>
                    <button onClick={() => openProfileDialog("wallet")}>{profilePayoutAddress ? t("Изменить") : t("Добавить")}</button>
                  </div>
                </div>
              </section>

              <section className="profile-section profile-purchases-section">
                <div className="profile-section-head">
                  <div className="profile-section-title">
                    <span><History size={19} /></span>
                    <div><small>{t("Покупки")}</small><h3>{t("История покупок")}</h3></div>
                  </div>
                  <button onClick={() => setActive("marketplace")}>{t("Открыть Маркет")}</button>
                </div>
                <div className="profile-purchase-list">
                  {[
                    [CURRENT_DEMO_TIER.name, `$${CURRENT_DEMO_TIER.priceUsd}`, "Тариф оформлен", "24 января"],
                    ["Продление активности", `$${SUBSCRIPTION_RULES.monthlyPriceUsd}`, "Активность продлена", "5 июля"],
                  ].map(([title, price, status, date]) => (
                    <div className="profile-purchase-row" key={title}>
                      <span><ShoppingBag size={17} /></span>
                      <div><strong>{t(title)}</strong><small>{t(date)} · {t(status)}</small></div>
                      <b>{price}</b>
                    </div>
                  ))}
                </div>
              </section>
            </div>

            <aside className="profile-settings-column">
              <section className="profile-section profile-access-section">
                <div className="profile-section-head">
                  <div className="profile-section-title">
                    <span><ShieldCheck size={19} /></span>
                    <div><small>{t("Доступ")}</small><h3>{t("Тариф и активность")}</h3></div>
                  </div>
                  <i className="profile-access-badge">{isActive ? t("Активна") : t("Неактивна")}</i>
                </div>
                <div className="profile-access-plan">
                  <div><span>{t("Тариф")}</span><strong>{tariffLabel}</strong></div>
                  <div><span>{t("Активность до")}</span><strong>{activityUntil}</strong></div>
                </div>
                <p>{t("Исторический статус сохраняется независимо от активности")}: <strong>{t(rankLabel)}</strong></p>
                <button className="profile-wide-button" onClick={onRenew}>{t("Продлить активность")}</button>
              </section>

              <section className="profile-section profile-security-section">
                <div className="profile-section-head">
                  <div className="profile-section-title">
                    <span><Lock size={19} /></span>
                    <div><small>{t("Аккаунт")}</small><h3>{t("Безопасность")}</h3></div>
                  </div>
                  <button onClick={() => openProfileDialog("security")}>{t("Настроить")}</button>
                </div>
                <button className="profile-action-row" onClick={() => openProfileDialog("security")}>
                  <span><Lock size={17} /></span><div><strong>{t("Пароль")}</strong><small>{t("Обновлен 12 дней назад")}</small></div><ChevronRight size={17} />
                </button>
                <button className="profile-action-row" onClick={() => openProfileDialog("security")}>
                  <span><Smartphone size={17} /></span><div><strong>{t("Активные устройства")}</strong><small>MacBook Pro · iPhone</small></div><ChevronRight size={17} />
                </button>
              </section>

              <section className="profile-section profile-notifications-section">
                <div className="profile-section-head">
                  <div className="profile-section-title">
                    <span><Bell size={19} /></span>
                    <div><small>{t("Связь")}</small><h3>{t("Уведомления")}</h3></div>
                  </div>
                </div>
                <div className="profile-notification-list">
                  {([
                    ["email", "Email", "Начисления, доступ и безопасность"],
                    ["push", "Push", "Задачи CRM и новые материалы"],
                  ] as const).map(([key, label, text]) => (
                    <button
                      type="button"
                      className="profile-toggle-row"
                      role="switch"
                      aria-checked={notificationSettings[key]}
                      key={key}
                      onClick={() => {
                        setNotificationSettings((settings) => ({ ...settings, [key]: !settings[key] }));
                        notify(`${t(label)}: ${t("настройки обновлены")}`);
                      }}
                    >
                      <div><strong>{t(label)}</strong><span>{t(text)}</span></div>
                      <i className={notificationSettings[key] ? "active" : ""}><b /></i>
                    </button>
                  ))}
                </div>
              </section>
            </aside>
          </div>
        </article>
      </section>

      {profileDialog === "data" ? (
        <PortalDialog title={t("Личные данные")} eyebrow={t("Настройки профиля")} onClose={closeProfileDialog} className="profile-edit-dialog" closeLabel={t("Закрыть")}>
          <div className="profile-edit-grid">
            {([
              ["name", "Имя"],
              ["surname", "Фамилия"],
              ["phone", "Телефон"],
              ["email", "Email"],
              ["city", "Город"],
            ] as const).map(([key, label]) => (
              <label key={key}><span>{t(label)}</span><input value={profileDraft[key]} onChange={(event) => setProfileDraft((draft) => ({ ...draft, [key]: event.target.value }))} /></label>
            ))}
          </div>
          <footer className="portal-dialog-actions">
            <button onClick={closeProfileDialog}>{t("Отмена")}</button>
            <button onClick={async () => {
              setProfileData(profileDraft);
              try {
                await updateProfile({
                  first_name: profileDraft.name,
                  last_name: profileDraft.surname,
                  phone: profileDraft.phone,
                  city: profileDraft.city,
                  country: profileDraft.country,
                  language: profileDraft.language.startsWith("En") ? "en" : profileDraft.language.startsWith("Es") ? "es" : "ru",
                });
                await refreshMe();
                notify(t("Личные данные сохранены"));
              } catch (err) {
                notify(err instanceof ApiError ? err.message : t("Не удалось сохранить профиль"));
              }
              closeProfileDialog();
            }}>{t("Сохранить изменения")}</button>
          </footer>
        </PortalDialog>
      ) : null}

      {profileDialog === "wallet" ? (
        <PortalDialog title={t("Адрес для выплат")} eyebrow={t("Платёжные реквизиты")} onClose={closeProfileDialog} className="withdraw-dialog" closeLabel={t("Закрыть")}>
          <section className="withdraw-network-card">
            <span className="withdraw-asset-mark">₮</span>
            <div><small>{t("Актив")}</small><strong>USDT</strong><p>{t("Сеть вывода пока не утверждена.")}</p></div>
            <em><ShieldCheck size={15} /> {t("Реквизит")}</em>
          </section>
          <label className="withdraw-address">
            <span>{t("Адрес USDT-кошелька")}</span>
            <div>
              <WalletCards size={18} />
              <input value={profilePayoutAddressDraft} onChange={(event) => setProfilePayoutAddressDraft(event.target.value.trim())} placeholder={t("Введите адрес USDT")} autoComplete="off" spellCheck={false} />
              <button type="button" onClick={async () => {
                try {
                  setProfilePayoutAddressDraft((await navigator.clipboard.readText()).trim());
                } catch {
                  notify(t("Не удалось прочитать буфер обмена"));
                }
              }}><ClipboardPaste size={16} /> {t("Вставить")}</button>
            </div>
            <small>{t("Сеть и формат адреса будут проверяться при оформлении заявки после утверждения правил вывода.")}</small>
          </label>
          <div className="withdraw-warning"><AlertTriangle size={18} /><p>{t("Перед сохранением сверьте адрес в приложении вашего криптокошелька.")}</p></div>
          <footer className="portal-dialog-actions">
            <button onClick={closeProfileDialog}>{t("Отмена")}</button>
            <button disabled={!profilePayoutAddressDraft.trim()} onClick={() => {
              const normalizedAddress = profilePayoutAddressDraft.trim();
              window.localStorage.setItem(PAYOUT_ADDRESS_STORAGE_KEY, normalizedAddress);
              setProfilePayoutAddress(normalizedAddress);
              closeProfileDialog();
              notify(t("Адрес для выплат сохранён"));
            }}>{t("Сохранить адрес")}</button>
          </footer>
        </PortalDialog>
      ) : null}

      {profileDialog === "security" ? (
        <PortalDialog title={t("Безопасность")} eyebrow={t("Защита аккаунта")} onClose={closeProfileDialog} className="security-dialog" closeLabel={t("Закрыть")}>
          <div className="security-options">
            {[
              ["Пароль", "Обновлён 12 дней назад", Lock],
              ["Активные устройства", "MacBook Pro · iPhone", Smartphone],
            ].map(([title, meta, OptionIcon]) => {
              const Icon = OptionIcon as typeof Lock;
              return <button key={title as string} onClick={() => notify(`${t(title as string)}: ${t("настройки открыты")}`)}><Icon size={19} /><div><strong>{t(title as string)}</strong><span>{t(meta as string)}</span></div><ChevronRight size={17} /></button>;
            })}
          </div>
        </PortalDialog>
      ) : null}
    </PageShell>
  );
}
