"use client";

import { useMemo, useState } from "react";
import { Check, ChevronRight, Info, Trophy } from "lucide-react";
import { usePortalBackend } from "../../../lib/auth/PortalBackendProvider";
import { PARTNER_RANKS, QUALIFICATION_PERIOD, RANK_QUALIFICATION_RULES } from "../../../lib/marketing-plan";
import type { TFn } from "../../../lib/portal/types";
import { PortalDialog } from "../shared/PortalDialog";

const RANK_GROUPS = [
  { title: "Партнёры", start: 0, end: 3 },
  { title: "Эксперты", start: 3, end: 6 },
  { title: "Мастера", start: 6, end: 9 },
  { title: "Лидеры", start: 9, end: 12 },
  { title: "Менторы", start: 12, end: 15 },
  { title: "Высшая ступень", start: 15, end: 16 },
] as const;

function rankIndexByName(name?: string | null): number {
  if (!name) return 0;
  const index = PARTNER_RANKS.findIndex((rank) => rank.name === name);
  return index >= 0 ? index : 0;
}

export function StatusLadderDialog({ onClose, t }: { onClose: () => void; t: TFn }) {
  const { dashboard } = usePortalBackend();
  const partner = dashboard?.partner as {
    tariff_id?: string | null;
    current_rank?: string | null;
    current_rank_name?: string;
    next_rank_name?: string;
  } | undefined;
  const metrics = dashboard?.metrics as {
    weekly_collapsed_pv?: { current?: number; required?: number; next_rank?: string };
  } | undefined;

  const isPartner = dashboard?.is_partner === true && Boolean(partner?.tariff_id);
  // Без тарифа текущий статус — Member (ещё не на лестнице PARTNER_RANKS).
  const currentRankIndex = isPartner ? rankIndexByName(partner?.current_rank_name) : -1;
  const nextRankIndex = isPartner
    ? Math.min(PARTNER_RANKS.length - 1, currentRankIndex + 1)
    : 0;
  const weeklyCollapsedPv = Number(metrics?.weekly_collapsed_pv?.current ?? 0);
  const nextRankRequired = isPartner
    ? (Number(
        metrics?.weekly_collapsed_pv?.required ?? PARTNER_RANKS[nextRankIndex].weeklyCollapsedPv,
      ) || PARTNER_RANKS[nextRankIndex].weeklyCollapsedPv)
    : 0;
  const currentRankName = isPartner
    ? (partner?.current_rank_name || PARTNER_RANKS[Math.max(0, currentRankIndex)].name)
    : "Member";
  const nextRankName = isPartner
    ? (metrics?.weekly_collapsed_pv?.next_rank
      || partner?.next_rank_name
      || PARTNER_RANKS[nextRankIndex].name)
    : (partner?.next_rank_name || "Партнёр I");
  const progressPct = isPartner && nextRankRequired > 0
    ? Math.min(100, Math.round((weeklyCollapsedPv / nextRankRequired) * 100))
    : 0;

  const [selectedRank, setSelectedRank] = useState<number | null>(null);
  const activeRank = selectedRank ?? nextRankIndex;

  const selectedGroup = useMemo(
    () => RANK_GROUPS.find((group) => activeRank >= group.start && activeRank < group.end) ?? RANK_GROUPS[0],
    [activeRank],
  );
  const selectedRule = PARTNER_RANKS[activeRank];
  const selectedQualifierNote = activeRank === 0
    ? "Партнёр I присваивается после покупки любого партнёрского тарифа."
    : activeRank <= 5
      ? `Считаются только лично приглашённые активные партнёры любого из ${RANK_QUALIFICATION_RULES.personalPartnerRanks.eligibleTierIds.length === 3 ? "трёх" : RANK_QUALIFICATION_RULES.personalPartnerRanks.eligibleTierIds.length} тарифов.`
      : `Нужны ${RANK_QUALIFICATION_RULES.binaryLegQualifierRanks.distinctPartners} разных активных квалификатора: по одному в каждой бинарной ноге, на любой физической глубине, уже имеющие требуемый статус.`;

  const rankState = (index: number) => {
    if (currentRankIndex >= 0 && index < currentRankIndex) return "achieved" as const;
    if (currentRankIndex >= 0 && index === currentRankIndex) return "current" as const;
    if (index === nextRankIndex) return "next" as const;
    return "future" as const;
  };

  const selectedState = rankState(activeRank);
  const selectedStateLabel =
    selectedState === "achieved" || selectedState === "current"
      ? t("Достигнут навсегда")
      : selectedState === "next"
        ? t("В работе")
        : t("Будущий статус");

  return (
    <PortalDialog title={t("Карьерная лестница")} eyebrow="RE:RISE · 16 статусов" onClose={onClose} className="rank-dialog" closeLabel={t("Закрыть")}>
      <div className="rank-dialog-summary">
        <div><span>{t("Текущий статус")}</span><strong>{t(currentRankName)}</strong></div>
        <div className="rank-summary-line"><i /><b style={{ width: `${progressPct}%` }} /></div>
        <div>
          <span>{t("Следующая ступень")}</span>
          <strong>
            {!isPartner
              ? t(nextRankName)
              : currentRankIndex >= PARTNER_RANKS.length - 1
                ? t("Максимум")
                : `${weeklyCollapsedPv} / ${nextRankRequired} PV · ${t(nextRankName)}`}
          </strong>
        </div>
      </div>
      <div className="rank-dialog-layout">
        <div className="rank-groups">
          {RANK_GROUPS.map((group) => (
            <section className="rank-family" key={group.title}>
              <span>{t(group.title)}</span>
              <div>
                {PARTNER_RANKS.slice(group.start, group.end).map((rank, offset) => {
                  const index = group.start + offset;
                  const state = rankState(index);
                  return (
                    <button
                      className={`${activeRank === index ? "selected " : ""}${state === "achieved" || state === "current" ? "current" : state === "next" ? "next" : "future"}`}
                      key={rank.name}
                      onClick={() => setSelectedRank(index)}
                      type="button"
                    >
                      <i>{state === "achieved" || state === "current" ? <Check size={14} /> : String(index + 1).padStart(2, "0")}</i>
                      <span>{t(rank.name)}</span>
                      {state === "current" ? <em>{t("Текущий")}</em> : state === "next" ? <em>{t("Следующий")}</em> : <ChevronRight size={15} />}
                    </button>
                  );
                })}
              </div>
            </section>
          ))}
        </div>
        <aside className="rank-detail-card">
          <span>{t(selectedGroup.title)} · {String(activeRank + 1).padStart(2, "0")} / 16</span>
          <div className={`rank-detail-mark ${selectedState === "achieved" || selectedState === "current" ? "current" : selectedState === "next" ? "next" : "future"}`}><Trophy size={28} /></div>
          <h3>{t(selectedRule.name)}</h3>
          <p>{t(selectedRule.requirement)}</p>
          <div className="rank-detail-meta"><span>{t("Схлоп за неделю")}</span><strong>{selectedRule.weeklyCollapsedPv.toLocaleString("ru-RU")} PV</strong></div>
          {selectedState === "next" ? (
            <div className="rank-detail-meta">
              <span>{t("Прогресс недели")}</span>
              <strong>{weeklyCollapsedPv} / {nextRankRequired} PV</strong>
            </div>
          ) : null}
          <div className="rank-detail-meta"><span>{t("Дополнительное условие")}</span><strong>{t(selectedRule.requirement)}</strong></div>
          <div className="rank-detail-meta"><span>{t("Разовая премия")}</span><strong>${selectedRule.rewardUsd.toLocaleString("ru-RU")}</strong></div>
          <div className="rank-detail-meta"><span>{t("Состояние")}</span><strong>{selectedStateLabel}</strong></div>
          <div className="marketing-plan-notice"><Info size={17} /><p>{t(selectedQualifierNote)}</p></div>
          <small>{t("Квалификационная неделя")}: {t(QUALIFICATION_PERIOD.starts)} — {t(QUALIFICATION_PERIOD.ends)} · МСК. {t("Регулярного подтверждения статуса нет.")}</small>
        </aside>
      </div>
    </PortalDialog>
  );
}
