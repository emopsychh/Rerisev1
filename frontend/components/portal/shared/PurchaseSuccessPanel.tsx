"use client";

import { CheckCircle2 } from "lucide-react";
import type { TFn } from "../../../lib/portal/types";

export type PurchaseSuccessInfo = {
  headline: string;
  message: string;
  status: string;
  amount?: string;
  orderId?: number;
  paymentHint?: string | null;
};

export function PurchaseSuccessPanel({
  info,
  t,
  onDone,
  doneLabel,
}: {
  info: PurchaseSuccessInfo;
  t: TFn;
  onDone: () => void;
  doneLabel?: string;
}) {
  return (
    <div className="purchase-ready purchase-success">
      <span aria-hidden="true"><CheckCircle2 size={34} /></span>
      <h3>{t(info.headline)}</h3>
      <p>{t(info.message)}</p>
      <div><span>{t("Статус")}</span><strong>{t(info.status)}</strong></div>
      {info.amount ? <div><span>{t("Сумма")}</span><strong>{info.amount}</strong></div> : null}
      {info.orderId ? <div><span>{t("Заказ")}</span><strong>#{info.orderId}</strong></div> : null}
      {info.paymentHint ? <p className="purchase-success-hint">{t(info.paymentHint)}</p> : null}
      <button type="button" onClick={onDone}>{t(doneLabel || "Готово")}</button>
    </div>
  );
}
