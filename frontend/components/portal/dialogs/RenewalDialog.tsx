"use client";

import { useState } from "react";
import { CheckCircle2, ChevronRight, RefreshCw, ShieldCheck } from "lucide-react";
import { renewPartner } from "../../../lib/api/partner";
import { ApiError } from "../../../lib/api/types";
import { usePortalBackend } from "../../../lib/auth/PortalBackendProvider";
import { PARTNER_TIERS, SUBSCRIPTION_RULES, type PartnerTierId } from "../../../lib/marketing-plan";
import { formatApiDate } from "../../../lib/portal";
import type { NotifyFn, TFn } from "../../../lib/portal/types";
import { PortalDialog } from "../shared/PortalDialog";
import { PurchaseSuccessPanel, type PurchaseSuccessInfo } from "../shared/PurchaseSuccessPanel";

function pvDepthForTier(tariffId?: string | null): number {
  if (tariffId && tariffId in SUBSCRIPTION_RULES.pvDepthByTier) {
    return SUBSCRIPTION_RULES.pvDepthByTier[tariffId as PartnerTierId];
  }
  return SUBSCRIPTION_RULES.pvDepthByTier.rise;
}

export function RenewalDialog({ onClose, notify, t }: { onClose: () => void; notify: NotifyFn; t: TFn }) {
  const { dashboard, wallet, reload } = usePortalBackend();
  const [step, setStep] = useState<"details" | "confirm" | "success">("details");
  const [submitting, setSubmitting] = useState(false);
  const [successInfo, setSuccessInfo] = useState<PurchaseSuccessInfo | null>(null);

  const partner = dashboard?.partner as {
    tariff_id?: string;
    tariff_name?: string;
    activity_until?: string;
  } | undefined;
  const hasTariff = Boolean(partner?.tariff_id);
  const canRenew = hasTariff && dashboard?.can_renew !== false;
  const tariffId = partner?.tariff_id ?? null;
  const tariffName =
    partner?.tariff_name
    || PARTNER_TIERS.find((tier) => tier.id === tariffId)?.name
    || t("Партнёрский тариф");
  const activityUntil = formatApiDate(partner?.activity_until, "—");
  const pvDepth = pvDepthForTier(tariffId);
  const priceUsd = SUBSCRIPTION_RULES.monthlyPriceUsd;
  const availableUsd = Number(
    (wallet?.balance as { available_usd?: number } | undefined)?.available_usd ?? 0,
  );
  const canPayWallet = canRenew && availableUsd >= priceUsd;

  const submitRenewal = async () => {
    if (submitting) return;
    if (!canRenew) {
      notify(t("Продление недоступно — сначала оформите тариф"));
      return;
    }
    setSubmitting(true);
    try {
      const order = await renewPartner();
      const paidFromWallet = order.status === "paid" && order.payment?.provider === "wallet";
      if (!paidFromWallet && order.payment?.payment_url) {
        window.open(order.payment.payment_url, "_blank", "noopener,noreferrer");
      }
      setSuccessInfo({
        headline: paidFromWallet ? "Активность продлена" : "Заявка на продление создана",
        message: paidFromWallet
          ? "Оплата с баланса прошла успешно. Срок активности удлинён на месяц."
          : "Заказ создан. Завершите оплату по счёту — после этого активность продлится.",
        status: paidFromWallet ? "Оплачено" : "Ожидает оплаты",
        amount: `$${priceUsd}`,
        orderId: order.order_id,
        paymentHint: paidFromWallet
          ? null
          : "Внешний счёт открыт в новой вкладке, если браузер не заблокировал окно.",
      });
      setStep("success");
      await reload();
    } catch (error) {
      const message = error instanceof ApiError ? error.message : t("Не удалось оформить продление");
      notify(message);
    } finally {
      setSubmitting(false);
    }
  };

  const dialogTitle =
    step === "success"
      ? t("Готово")
      : step === "confirm"
        ? t("Подтверждение")
        : t("Продление активности");

  return (
    <PortalDialog title={dialogTitle} eyebrow={t("Партнёрская подписка")} onClose={onClose} className="renewal-dialog" closeLabel={t("Закрыть")}>
      {step === "success" && successInfo ? (
        <PurchaseSuccessPanel info={successInfo} t={t} onDone={onClose} />
      ) : step === "details" ? (
        <>
          <section className="renewal-summary">
            <div className="renewal-plan-icon"><RefreshCw size={24} /></div>
            <div><span>{t("Текущий тариф")}</span><h3>{tariffName}</h3><p>{t("Ежемесячное продление партнёрской активности.")}</p></div>
            <div className="renewal-price"><strong>${priceUsd}</strong><span>{t("за продление")}</span></div>
          </section>
          <div className="renewal-dates">
            <div><span>{t("Активность до")}</span><strong>{activityUntil}</strong></div>
            <ChevronRight size={18} />
            <div><span>{t("Новый срок")}</span><strong>{t("+1 месяц после оплаты")}</strong></div>
          </div>
          {!hasTariff ? (
            <p className="renewal-unavailable">{t("Сначала купите партнёрский тариф в маркете.")}</p>
          ) : (
            <div className="marketing-plan-notice">
              <ShieldCheck size={17} />
              <p>{canPayWallet
                ? t(`На кошельке $${availableUsd.toFixed(2)} — хватит. Продление спишется с баланса сразу, срок удлинится от текущей даты активности.`)
                : t(`Баланс кошелька: $${availableUsd.toFixed(2)}. При нехватке средств будет создан внешний счёт. Раннее продление удлиняет текущий срок.`)}</p>
            </div>
          )}
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
            <button type="button" disabled={!canRenew} onClick={() => setStep("confirm")}>
              {t("Перейти к подтверждению")}<ChevronRight size={17} />
            </button>
          </footer>
        </>
      ) : (
        <div className="purchase-ready">
          <span><CheckCircle2 size={34} /></span>
          <h3>{t("Подтвердите продление")}</h3>
          <p>{canPayWallet
            ? t("С баланса спишется $30, активность удлинится на месяц.")
            : t("Проверьте условия перед оформлением. При нехватке баланса откроется внешний счёт.")}</p>
          <div><span>{t("Тариф")}</span><strong>{tariffName}</strong></div>
          <div><span>{t("Период")}</span><strong>{t("Ежемесячное продление")}</strong></div>
          <div><span>{t("Сумма")}</span><strong>${priceUsd}</strong></div>
          <div><span>{t("Оплата")}</span><strong>{canPayWallet ? t("С баланса") : t("Внешний счёт / баланс")}</strong></div>
          <div><span>{t("Подписочный PV")}</span><strong>{SUBSCRIPTION_RULES.generatedPv} PV · {t(`до ${pvDepth} физических уровней`)}</strong></div>
          <footer className="portal-dialog-actions">
            <button type="button" disabled={submitting} onClick={() => setStep("details")}>{t("Назад")}</button>
            <button type="button" disabled={submitting || !canRenew} onClick={() => void submitRenewal()}>
              {submitting
                ? t("Оформляем…")
                : (canPayWallet ? t("Оплатить с баланса") : t("Оформить продление"))}
            </button>
          </footer>
        </div>
      )}
    </PortalDialog>
  );
}
