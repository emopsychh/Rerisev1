"use client";

import { startTransition, useEffect, useState } from "react";
import { Check, Trophy, UserPlus } from "lucide-react";
import { useAuth } from "../../../lib/auth/AuthProvider";
import { usePortalBackend } from "../../../lib/auth/PortalBackendProvider";
import { BINARY_RULES } from "../../../lib/marketing-plan";
import { formatApiDate, formatUsd } from "../../../lib/portal";
import type { NotifyFn, SectionId, TFn } from "../../../lib/portal";
import { PageShell } from "../shared/PageShell";
import { PortalLoading } from "../shared/PortalLoading";
import { PartnersView } from "./PartnersView";

export function CabinetView({ setActive, t, notify, onInvite, onOpenRanks }: { setActive: (id: SectionId) => void; t: TFn; notify: NotifyFn; onInvite: () => void; onOpenRanks: () => void }) {
  const { user } = useAuth();
  const { dashboard, wallet, ready } = usePortalBackend();
  const [teamVisible, setTeamVisible] = useState(false);
  const isPartner = dashboard?.is_partner !== false && Boolean(dashboard?.partner || dashboard?.is_partner);
  const partner = dashboard?.partner as {
    tariff_name?: string;
    current_rank_name?: string;
    next_rank_name?: string;
    activity_until?: string;
  } | undefined;
  const metrics = dashboard?.metrics as {
    weekly_collapsed_pv?: { current?: number; required?: number; next_rank?: string };
    active_personal_partners?: { current?: number; required?: number };
    fast_start?: { current?: number; required?: number; reward_usd?: number; reward_paid?: boolean };
    available_to_withdraw?: { amount_usd?: number };
  } | undefined;
  const qualification = dashboard?.qualification_week as {
    title?: string;
    week_end?: string;
    rows?: Array<{ label?: string; current?: number; required?: number; unit?: string }>;
  } | undefined;
  const weeklyCollapsedPv = Number(metrics?.weekly_collapsed_pv?.current ?? 0);
  const nextRankRequired = Number(metrics?.weekly_collapsed_pv?.required ?? 0);
  const personalCurrent = Number(metrics?.active_personal_partners?.current ?? 0);
  const personalRequired = Number(metrics?.active_personal_partners?.required ?? 0);
  const personalProgress = personalRequired > 0
    ? Math.min(100, Math.round((personalCurrent / personalRequired) * 100))
    : 0;
  const fastStart = metrics?.fast_start;
  const rankProgress = nextRankRequired > 0
    ? Math.min(100, Math.round((weeklyCollapsedPv / nextRankRequired) * 100))
    : 0;
  const binaryIncomeRow = Array.isArray(qualification?.rows)
    ? qualification.rows.find((row) => row?.unit === "USD" || String(row?.label || "").toLowerCase().includes("бинар"))
    : undefined;
  const binaryIncome = Number(
    binaryIncomeRow?.current
    ?? (nextRankRequired > 0 || weeklyCollapsedPv > 0 ? weeklyCollapsedPv / BINARY_RULES.collapsedPvPerUsd : 0),
  );
  const availableUsd = Number(
    metrics?.available_to_withdraw?.amount_usd
      ?? (dashboard?.balance as { available_usd?: number } | undefined)?.available_usd
      ?? (wallet?.balance as { available_usd?: number } | undefined)?.available_usd
      ?? 0,
  );
  const displayName = [user?.first_name, user?.last_name].filter(Boolean).join(" ") || "Партнёр";
  const currentRankName = partner?.current_rank_name || "—";
  const nextRankName = metrics?.weekly_collapsed_pv?.next_rank || partner?.next_rank_name || "—";
  const activityUntil = formatApiDate(partner?.activity_until, "—");
  const [qualificationTimeLeft, setQualificationTimeLeft] = useState({ days: 0, hours: 0, minutes: 0, seconds: 0 });

  useEffect(() => {
    if (!qualification?.week_end) {
      setQualificationTimeLeft({ days: 0, hours: 0, minutes: 0, seconds: 0 });
      return;
    }
    const qualificationEndsAt = new Date(`${qualification.week_end}T23:59:59+03:00`).getTime();
    const updateCountdown = () => {
      const remaining = Math.max(0, qualificationEndsAt - Date.now());
      setQualificationTimeLeft({
        days: Math.floor(remaining / 86_400_000),
        hours: Math.floor((remaining % 86_400_000) / 3_600_000),
        minutes: Math.floor((remaining % 3_600_000) / 60_000),
        seconds: Math.floor((remaining % 60_000) / 1_000),
      });
    };

    updateCountdown();
    const timer = window.setInterval(updateCountdown, 1_000);
    return () => window.clearInterval(timer);
  }, [qualification?.week_end]);

  useEffect(() => {
    const frame = window.requestAnimationFrame(() => {
      startTransition(() => setTeamVisible(true));
    });
    return () => window.cancelAnimationFrame(frame);
  }, []);

  const countdownPart = (value: number) => String(value).padStart(2, "0");

  if (!ready) {
    return (
      <PageShell className="cabinet-unified-shell">
        <PortalLoading label={t("Загрузка кабинета…")} />
      </PageShell>
    );
  }

  return (
    <PageShell className="cabinet-unified-shell">
      <section className="cabinet-grid cabinet-unified-grid">
        <article className="cabinet-hero cabinet-partner-card">
          <div className="partner-card-aura" aria-hidden="true" />
          <div className="partner-card-top">
            <div className="partner-card-mark" aria-hidden="true">
              <span>R</span>
              <div>
                <strong>RE:RISE</strong>
                <small>{String(dashboard?.member_label || (isPartner ? "PARTNER" : "MEMBER"))}</small>
              </div>
            </div>
          </div>
          <div className="partner-card-main">
            <div>
              <h2>{displayName}</h2>
            </div>
          </div>
          <div className="rank-line" aria-label={t("Прогресс статуса")}>
            <span className="rank-current">{t(currentRankName)}</span>
            <i role="progressbar" aria-valuemin={0} aria-valuemax={nextRankRequired} aria-valuenow={weeklyCollapsedPv}><b style={{ width: `${rankProgress}%` }} /></i>
            <span className="rank-next">{t(nextRankName)}</span>
          </div>
          <div className="partner-card-bottom">
            <div className="partner-card-balance">
              <span>{t("Баланс")}</span>
              <button
                className="partner-card-balance-link"
                type="button"
                onClick={() => setActive("wallet")}
                aria-label={t("Открыть кошелек")}
              >
                <strong>{formatUsd(availableUsd, "$0")}</strong>
              </button>
            </div>
            <div className="partner-card-active">
              <span className="partner-card-active-label">{t("Активен до")}</span>
              <strong>{activityUntil}</strong>
            </div>
          </div>
        </article>

        <article className="cabinet-rank-card">
          <header>
            <div><span>{t("Квалификация")}</span><h3>{t(qualification?.title || "Квалификационная неделя")}</h3></div>
            <div className="cabinet-qualification-countdown" aria-label={t("До конца квалификационной недели")}>
              <small>{t("До конца недели")}</small>
              <strong>
                <span><b>{countdownPart(qualificationTimeLeft.days)}</b>{t("д")}</span>
                <i>:</i>
                <span><b>{countdownPart(qualificationTimeLeft.hours)}</b>{t("ч")}</span>
                <i>:</i>
                <span><b>{countdownPart(qualificationTimeLeft.minutes)}</b>{t("м")}</span>
                <i>:</i>
                <span><b>{countdownPart(qualificationTimeLeft.seconds)}</b>{t("с")}</span>
              </strong>
            </div>
          </header>
          <div className="cabinet-rank-main">
            <div className="cabinet-rank-metrics">
              <div className="cabinet-rank-metric">
                <span>{t("Недельный объём")}</span>
                <strong>{weeklyCollapsedPv} / {nextRankRequired || "—"} <small>PV</small></strong>
                <i><b style={{ width: `${rankProgress}%` }} /></i>
                <small>
                  {nextRankRequired > 0
                    ? `${t("Осталось")} ${Math.max(0, nextRankRequired - weeklyCollapsedPv)} PV`
                    : t("Нет следующей ступени")}
                </small>
              </div>
              <div className="cabinet-rank-metric is-personal">
                <span>{t("Активные личные")}</span>
                <strong>{personalCurrent}{personalRequired > 0 ? ` / ${personalRequired}` : ""}</strong>
                <i><b style={{ width: `${personalProgress}%` }} /></i>
                <small>
                  {personalRequired <= 0
                    ? t("Условие не требуется")
                    : personalCurrent >= personalRequired
                      ? t("Условие выполнено")
                      : `${t("Осталось")} ${Math.max(0, personalRequired - personalCurrent)}`}
                </small>
              </div>
            </div>
            <div className="cabinet-rank-secondary">
              <div><span>{t("Бинарный доход недели")}</span><strong>${binaryIncome}</strong></div>
              <div>
                <span>{t("Быстрый старт")}</span>
                <strong>
                  {fastStart?.reward_paid
                    ? <>{t("выполнен")} <em>+${Number(fastStart.reward_usd ?? 0)}</em></>
                    : `${Number(fastStart?.current ?? 0)} / ${Number(fastStart?.required ?? 0)}`}
                </strong>
              </div>
              {fastStart?.reward_paid ? <span className="cabinet-rank-check"><Check size={17} /></span> : null}
            </div>
          </div>
          <footer>
            <button type="button" onClick={onInvite}><UserPlus size={17} />{t("Пригласить партнёра")}</button>
            <button type="button" onClick={onOpenRanks}><Trophy size={17} />{t("Все статусы")}</button>
          </footer>
        </article>

        <div className="cabinet-team-section">
          {teamVisible ? (
            <PartnersView t={t} notify={notify} embedded />
          ) : (
            <div className="cabinet-team-skeleton" aria-hidden="true" />
          )}
        </div>
      </section>
    </PageShell>
  );
}
