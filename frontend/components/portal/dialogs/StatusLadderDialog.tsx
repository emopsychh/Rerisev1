"use client";

import { useState } from "react";
import { Check, ChevronRight, Info, Trophy } from "lucide-react";
import { PARTNER_RANKS, QUALIFICATION_PERIOD, RANK_QUALIFICATION_RULES } from "../../../lib/marketing-plan";
import type { TFn } from "../../../lib/portal/types";
import { PortalDialog } from "../shared/PortalDialog";

export function StatusLadderDialog({ onClose, t }: { onClose: () => void; t: TFn }) {
  const [selectedRank, setSelectedRank] = useState(1);
  const weeklyCollapsedPv = 60;
  const rankGroups = [
    { title: "Партнёры", start: 0, end: 3 },
    { title: "Эксперты", start: 3, end: 6 },
    { title: "Мастера", start: 6, end: 9 },
    { title: "Лидеры", start: 9, end: 12 },
    { title: "Менторы", start: 12, end: 15 },
    { title: "Высшая ступень", start: 15, end: 16 },
  ];
  const selectedGroup = rankGroups.find((group) => selectedRank >= group.start && selectedRank < group.end) ?? rankGroups[0];
  const selectedRule = PARTNER_RANKS[selectedRank];
  const selectedQualifierNote = selectedRank === 0
    ? "Партнёр I присваивается после покупки любого партнёрского тарифа."
    : selectedRank <= 5
      ? `Считаются только лично приглашённые активные партнёры любого из ${RANK_QUALIFICATION_RULES.personalPartnerRanks.eligibleTierIds.length === 3 ? "трёх" : RANK_QUALIFICATION_RULES.personalPartnerRanks.eligibleTierIds.length} тарифов.`
      : `Нужны ${RANK_QUALIFICATION_RULES.binaryLegQualifierRanks.distinctPartners} разных активных квалификатора: по одному в каждой бинарной ноге, на любой физической глубине, уже имеющие требуемый статус.`;

  return (
    <PortalDialog title={t("Карьерная лестница")} eyebrow="RE:RISE · 16 статусов" onClose={onClose} className="rank-dialog" closeLabel={t("Закрыть")}>
      <div className="rank-dialog-summary">
        <div><span>{t("Текущий статус")}</span><strong>{t("Партнёр I")}</strong></div>
        <div className="rank-summary-line"><i /><b style={{ width: `${Math.min(100, Math.round((weeklyCollapsedPv / PARTNER_RANKS[1].weeklyCollapsedPv) * 100))}%` }} /></div>
        <div><span>{t("Следующая ступень")}</span><strong>{weeklyCollapsedPv} / {PARTNER_RANKS[1].weeklyCollapsedPv} PV</strong></div>
      </div>
      <div className="rank-dialog-layout">
        <div className="rank-groups">
          {rankGroups.map((group) => (
            <section className="rank-family" key={group.title}>
              <span>{t(group.title)}</span>
              <div>
                {PARTNER_RANKS.slice(group.start, group.end).map((rank, offset) => {
                  const index = group.start + offset;
                  return (
                    <button className={`${selectedRank === index ? "selected " : ""}${index === 0 ? "current" : index === 1 ? "next" : "future"}`} key={rank.name} onClick={() => setSelectedRank(index)}>
                      <i>{index === 0 ? <Check size={14} /> : String(index + 1).padStart(2, "0")}</i>
                      <span>{t(rank.name)}</span>
                      {index === 0 ? <em>{t("Текущий")}</em> : index === 1 ? <em>{t("Следующий")}</em> : <ChevronRight size={15} />}
                    </button>
                  );
                })}
              </div>
            </section>
          ))}
        </div>
        <aside className="rank-detail-card">
          <span>{t(selectedGroup.title)} · {String(selectedRank + 1).padStart(2, "0")} / 16</span>
          <div className={`rank-detail-mark ${selectedRank === 0 ? "current" : selectedRank === 1 ? "next" : "future"}`}><Trophy size={28} /></div>
          <h3>{t(selectedRule.name)}</h3>
          <p>{t(selectedRule.requirement)}</p>
          <div className="rank-detail-meta"><span>{t("Схлоп за неделю")}</span><strong>{selectedRule.weeklyCollapsedPv.toLocaleString("ru-RU")} PV</strong></div>
          <div className="rank-detail-meta"><span>{t("Дополнительное условие")}</span><strong>{t(selectedRule.requirement)}</strong></div>
          <div className="rank-detail-meta"><span>{t("Разовая премия")}</span><strong>${selectedRule.rewardUsd.toLocaleString("ru-RU")}</strong></div>
          <div className="rank-detail-meta"><span>{t("Состояние")}</span><strong>{selectedRank === 0 ? t("Достигнут навсегда") : selectedRank === 1 ? t("В работе") : t("Будущий статус")}</strong></div>
          <div className="marketing-plan-notice"><Info size={17} /><p>{t(selectedQualifierNote)}</p></div>
          <small>{t("Квалификационная неделя")}: {t(QUALIFICATION_PERIOD.starts)} — {t(QUALIFICATION_PERIOD.ends)} · МСК. {t("Регулярного подтверждения статуса нет.")}</small>
        </aside>
      </div>
    </PortalDialog>
  );
}
