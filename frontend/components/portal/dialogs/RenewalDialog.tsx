"use client";

import { useState } from "react";
import { CheckCircle2, ChevronRight, RefreshCw } from "lucide-react";
import { renewPartner } from "../../../lib/api/partner";
import { ApiError } from "../../../lib/api/types";
import { usePortalBackend } from "../../../lib/auth/PortalBackendProvider";
import { PARTNER_TIERS, SUBSCRIPTION_RULES, type PartnerTierId } from "../../../lib/marketing-plan";
import { formatApiDate } from "../../../lib/portal";
import type { NotifyFn, TFn } from "../../../lib/portal/types";
import { PortalDialog } from "../shared/PortalDialog";

function pvDepthForTier(tariffId?: string | null): number {
  if (tariffId && tariffId in SUBSCRIPTION_RULES.pvDepthByTier) {
    return SUBSCRIPTION_RULES.pvDepthByTier[tariffId as PartnerTierId];
  }
  return SUBSCRIPTION_RULES.pvDepthByTier.rise;
}

export function RenewalDialog({ onClose, notify, t }: { onClose: () => void; notify: NotifyFn; t: TFn }) {
  const { dashboard, reload } = usePortalBackend();
  const [isConfirmationStep, setIsConfirmationStep] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const partner = dashboard?.partner as {
    tariff_id?: string;
    tariff_name?: string;
    activity_until?: string;
  } | undefined;
  const canRenew = dashboard?.can_renew === true;
  const tariffId = partner?.tariff_id ?? null;
  const tariffName =
    partner?.tariff_name
    || PARTNER_TIERS.find((tier) => tier.id === tariffId)?.name
    || t("Партнёрский тариф");
  const activityUntil = formatApiDate(partner?.activity_until, "—");
  const pvDepth = pvDepthForTier(tariffId);

  const submitRenewal = async () => {
    if (submitting) return;
    if (!canRenew) {
      notify(t("Продление пока недоступно"));
      return;
    }
    setSubmitting(true);
    try {
      const order = await renewPartner();
      const paidFromWallet = order.status === "paid" && order.payment?.provider === "wallet";
      if (paidFromWallet) {
        notify(t("Активность продлена с баланса"));
      } else if (order.payment?.payment_url) {
        window.open(order.payment.payment_url, "_blank", "noopener,noreferrer");
        notify(t("Заявка на продление создана. Завершите оплату."));
      } else {
        notify(order.payment?.instructions || t("Заявка на продление оформлена"));
      }
      await reload();
      onClose();
    } catch (error) {
      const message = error instanceof ApiError ? error.message : t("Не удалось оформить продление");
      notify(message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <PortalDialog title={t("Продление активности")} eyebrow={t("Партнёрская подписка")} onClose={onClose} className="renewal-dialog" closeLabel={t("Закрыть")}>
      {!isConfirmationStep ? (
        <>
          <section className="renewal-summary">
            <div className="renewal-plan-icon"><RefreshCw size={24} /></div>
            <div><span>{t("Текущий тариф")}</span><h3>{tariffName}</h3><p>{t("Ежемесячное продление партнёрской активности.")}</p></div>
            <div className="renewal-price"><strong>${SUBSCRIPTION_RULES.monthlyPriceUsd}</strong><span>{t("за продление")}</span></div>
          </section>
          <div className="renewal-dates">
            <div><span>{t("Активность до")}</span><strong>{activityUntil}</strong></div>
            <ChevronRight size={18} />
            <div><span>{t("Новый срок")}</span><strong>{t("После оплаты")}</strong></div>
          </div>
          {!canRenew ? (
            <p className="renewal-unavailable">{t("Продление доступно в окне перед окончанием активности.")}</p>
          ) : null}
          <section className="renewal-includes">
            {[
              `Прямому активному спонсору начисляется $${SUBSCRIPTION_RULES.directSponsorRewardUsd}`,
              `Продление создаёт ${SUBSCRIPTION_RULES.generatedPv} PV`,
              `Подписочный PV учитывается до ${pvDepth} физических уровней`,
              "Первый включённый месяц не считается отдельным продлением",
            ].map((item) => <span key={item}><CheckCircle2 size={16} />{t(item)}</span>)}
          </section>
          <footer className="portal-dialog-actions">
            <button type="button" onClick={onClose}>{t("Отмена")}</button>
            <button type="button" disabled={!canRenew} onClick={() => setIsConfirmationStep(true)}>
              {t("Перейти к подтверждению")}<ChevronRight size={17} />
            </button>
          </footer>
        </>
      ) : (
        <div className="purchase-ready">
          <span><CheckCircle2 size={34} /></span>
          <h3>{t("Подтвердите заявку на продление")}</h3>
          <p>{t("Проверьте условия перед оформлением заявки.")}</p>
          <div><span>{t("Тариф")}</span><strong>{tariffName}</strong></div>
          <div><span>{t("Период")}</span><strong>{t("Ежемесячное продление")}</strong></div>
          <div><span>{t("Сумма")}</span><strong>${SUBSCRIPTION_RULES.monthlyPriceUsd}</strong></div>
          <div><span>{t("Подписочный PV")}</span><strong>{SUBSCRIPTION_RULES.generatedPv} PV · {t(`до ${pvDepth} физических уровней`)}</strong></div>
          <footer className="portal-dialog-actions">
            <button type="button" disabled={submitting} onClick={() => setIsConfirmationStep(false)}>{t("Назад")}</button>
            <button type="button" disabled={submitting || !canRenew} onClick={() => void submitRenewal()}>
              {submitting ? t("Оформляем…") : t("Оформить заявку")}
            </button>
          </footer>
        </div>
      )}
    </PortalDialog>
  );
}
