"use client";

import { useState } from "react";
import { CheckCircle2, ChevronRight, RefreshCw } from "lucide-react";
import { CURRENT_DEMO_TIER, SUBSCRIPTION_RULES } from "../../../lib/marketing-plan";
import type { NotifyFn, TFn } from "../../../lib/portal/types";
import { PortalDialog } from "../shared/PortalDialog";

export function RenewalDialog({ onClose, notify, t }: { onClose: () => void; notify: NotifyFn; t: TFn }) {
  const [isConfirmationStep, setIsConfirmationStep] = useState(false);

  return (
    <PortalDialog title={t("Продление активности")} eyebrow={t("Партнёрская подписка")} onClose={onClose} className="renewal-dialog" closeLabel={t("Закрыть")}>
      {!isConfirmationStep ? (
        <>
          <section className="renewal-summary">
            <div className="renewal-plan-icon"><RefreshCw size={24} /></div>
            <div><span>{t("Текущий тариф")}</span><h3>{CURRENT_DEMO_TIER.name}</h3><p>{t("Ежемесячное продление партнёрской активности.")}</p></div>
            <div className="renewal-price"><strong>${SUBSCRIPTION_RULES.monthlyPriceUsd}</strong><span>{t("за продление")}</span></div>
          </section>
          <div className="renewal-dates">
            <div><span>{t("Активность до")}</span><strong>24.07.2026</strong></div>
            <ChevronRight size={18} />
            <div><span>{t("Новый срок")}</span><strong>{t("После подтверждения")}</strong></div>
          </div>
          <section className="renewal-includes">
            {[
              `Прямому активному спонсору начисляется $${SUBSCRIPTION_RULES.directSponsorRewardUsd}`,
              `Продление создаёт ${SUBSCRIPTION_RULES.generatedPv} PV`,
              `Для ${CURRENT_DEMO_TIER.name} подписочный PV учитывается до ${SUBSCRIPTION_RULES.pvDepthByTier[CURRENT_DEMO_TIER.id]} физических уровней`,
              "Первый включённый месяц не считается отдельным продлением",
              "Точная дата окончания будет рассчитана после утверждения календарного правила",
            ].map((item) => <span key={item}><CheckCircle2 size={16} />{t(item)}</span>)}
          </section>
          <footer className="portal-dialog-actions">
            <button onClick={onClose}>{t("Отмена")}</button>
            <button onClick={() => setIsConfirmationStep(true)}>{t("Перейти к подтверждению")}<ChevronRight size={17} /></button>
          </footer>
        </>
      ) : (
        <div className="purchase-ready">
          <span><CheckCircle2 size={34} /></span>
          <h3>{t("Подтвердите заявку на продление")}</h3>
          <p>{t("Проверьте утверждённые условия перед оформлением заявки.")}</p>
          <div><span>{t("Тариф")}</span><strong>{CURRENT_DEMO_TIER.name}</strong></div>
          <div><span>{t("Период")}</span><strong>{t("Ежемесячное продление")}</strong></div>
          <div><span>{t("Сумма")}</span><strong>${SUBSCRIPTION_RULES.monthlyPriceUsd}</strong></div>
          <div><span>{t("Подписочный PV")}</span><strong>{SUBSCRIPTION_RULES.generatedPv} PV · {t(`до ${SUBSCRIPTION_RULES.pvDepthByTier[CURRENT_DEMO_TIER.id]} физических уровней`)}</strong></div>
          <footer className="portal-dialog-actions">
            <button onClick={() => setIsConfirmationStep(false)}>{t("Назад")}</button>
            <button onClick={() => {
              onClose();
              notify(t("Заявка на продление оформлена"));
            }}>{t("Оформить заявку")}</button>
          </footer>
        </div>
      )}
    </PortalDialog>
  );
}
