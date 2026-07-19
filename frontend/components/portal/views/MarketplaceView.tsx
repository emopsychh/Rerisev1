"use client";

import { useEffect, useRef, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Check, ChevronRight, ShieldCheck, Sparkles, Zap } from "lucide-react";
import { usePortalBackend } from "../../../lib/auth/PortalBackendProvider";
import { createOrder } from "../../../lib/api/store";
import { ApiError } from "../../../lib/api/types";
import { marketOfferHref, routeSlug } from "../../../lib/portal";
import type { MarketOffer, MarketTab, NotifyFn, TFn } from "../../../lib/portal";
import { PageShell } from "../shared/PageShell";
import { PortalDialog } from "../shared/PortalDialog";
import { PortalLoading } from "../shared/PortalLoading";
import { PurchaseSuccessPanel, type PurchaseSuccessInfo } from "../shared/PurchaseSuccessPanel";

const TARIFF_RANK: Record<string, number> = {
  rise: 1,
  "rise-pro": 2,
  "rise-pro-max": 3,
};

function tariffRank(id?: string | null): number {
  if (!id) return 0;
  return TARIFF_RANK[id] ?? 0;
}

export function MarketplaceView({ t, notify, marketTab }: { t: TFn; notify: NotifyFn; marketTab: MarketTab }) {
  const router = useRouter();
  const pathname = usePathname();
  const { tariffs, tokens, reload, home, dashboard, ready, wallet } = usePortalBackend();
  const [selectedOffer, setSelectedOffer] = useState<MarketOffer | null>(null);
  const [purchaseStep, setPurchaseStep] = useState<"details" | "ready">("details");
  const [ordering, setOrdering] = useState(false);
  const [successInfo, setSuccessInfo] = useState<PurchaseSuccessInfo | null>(null);
  const successLockedRef = useRef(false);

  const availableUsd = Number(
    (wallet?.balance as { available_usd?: number } | undefined)?.available_usd ?? 0,
  );
  const currentTariffId = String(
    (dashboard?.partner as { tariff_id?: string } | undefined)?.tariff_id
    || home?.partner_summary?.tariff_id
    || "",
  ) || null;

  const resolvePackageOrderType = (productId: string): "purchase" | "upgrade" | null => {
    if (!currentTariffId) return "purchase";
    const current = tariffRank(currentTariffId);
    const target = tariffRank(productId);
    if (target <= 0) return "purchase";
    if (target > current) return "upgrade";
    return null;
  };

  const apiPackages = tariffs.map((item) => {
    const terms = (item.terms as Record<string, unknown> | undefined) || {};
    const personalBonus = Number(terms.personal_bonus_cap_usd ?? item.personal_bonus_cap_usd ?? 0);
    const binaryDepth = Number(terms.binary_depth ?? item.binary_depth ?? 0);
    const matchingLines = Number(terms.matching_lines ?? item.matching_lines ?? 0);
    const included = Array.isArray(item.included) ? item.included.map(String) : [];
    const matchingLabel = matchingLines === 1 ? "линия" : matchingLines < 5 ? "линии" : "линий";
    return {
      title: String(item.name || item.id),
      productId: String(item.id),
      price: `$${Number(item.price_usd || 0)}`,
      priceUsd: Number(item.price_usd || 0),
      // Не показываем «N PV» как привилегию покупателя — объём покупки идёт в сеть выше.
      pv: `${binaryDepth} ур. бинар`,
      text: String(item.description || ""),
      eyebrow: "RE:RISE",
      note: included[0] || String(item.quick_start || "Первый месяц партнёрской активности включён"),
      features: [
        `Личный бонус с приглашённых: до $${personalBonus}`,
        `Глубина бинара: ${binaryDepth} уровней`,
        `Матчинг: 10% · ${matchingLines} ${matchingLabel}`,
        ...included.slice(1),
      ],
      highlight: String(item.id).includes("pro") && !String(item.id).includes("max"),
    };
  });

  const apiTokens = tokens.map((item) => {
    const amount = Number(item.amount || 0);
    const priceUsd = Number(item.price_usd || 0);
    const tokensPerUsd = Number(
      item.tokens_per_usd
      ?? (priceUsd > 0 ? Math.round(amount / priceUsd) : 0),
    );
    return {
      title: String(item.name || `${amount.toLocaleString("ru-RU")} токенов`),
      productId: String(item.id),
      price: `$${priceUsd}`,
      priceUsd,
      amount,
      tokensPerUsd,
      text: `${amount.toLocaleString("ru-RU")} токенов · ${tokensPerUsd} ток./$1`,
      pv: "без PV",
      features: [
        `${amount.toLocaleString("ru-RU")} AI-токенов на баланс`,
        `Курс пакета: ${tokensPerUsd} токенов за $1`,
        "Используются только в AI Hub",
        "Не участвуют в PV, бинаре и партнёрских начислениях",
      ],
    };
  });
  const bestTokenRate = apiTokens.reduce(
    (best, pack) => Math.max(best, pack.tokensPerUsd),
    0,
  );

  const buildSuccessInfo = (
    offer: MarketOffer,
    order: { order_id: number; status: string; payment?: { provider?: string; payment_url?: string | null } },
    orderType: string,
  ): PurchaseSuccessInfo => {
    const paidFromWallet = order.status === "paid" && order.payment?.provider === "wallet";
    if (offer.kind === "tokens") {
      return {
        headline: paidFromWallet ? "Токены зачислены" : "Заказ токенов создан",
        message: paidFromWallet
          ? "Оплата с баланса прошла успешно. Токены уже на балансе AI Hub."
          : "Заказ создан. Завершите оплату по счёту — после этого токены появятся в AI Hub.",
        status: paidFromWallet ? "Оплачено" : "Ожидает оплаты",
        amount: offer.price,
        orderId: order.order_id,
        paymentHint: paidFromWallet ? null : "Внешний счёт открыт в новой вкладке, если браузер не заблокировал окно.",
      };
    }
    if (orderType === "upgrade") {
      return {
        headline: paidFromWallet ? "Апгрейд выполнен" : "Заявка на апгрейд создана",
        message: paidFromWallet
          ? `${offer.title} активирован. Срок текущей активности сохранён.`
          : `Заказ на апгрейд до ${offer.title} создан. Оплатите счёт, чтобы завершить переход.`,
        status: paidFromWallet ? "Оплачено" : "Ожидает оплаты",
        amount: offer.price,
        orderId: order.order_id,
        paymentHint: paidFromWallet ? null : "Внешний счёт открыт в новой вкладке, если браузер не заблокировал окно.",
      };
    }
    return {
      headline: paidFromWallet ? "Тариф активирован" : "Заказ тарифа создан",
      message: paidFromWallet
        ? `${offer.title} оплачен с баланса и уже активен.`
        : `Заказ на ${offer.title} создан. Оплатите счёт, чтобы активировать доступ.`,
      status: paidFromWallet ? "Оплачено" : "Ожидает оплаты",
      amount: offer.price,
      orderId: order.order_id,
      paymentHint: paidFromWallet ? null : "Внешний счёт открыт в новой вкладке, если браузер не заблокировал окно.",
    };
  };

  const placeOrder = async (productId: string, orderType = "purchase") => {
    if (!selectedOffer) return;
    setOrdering(true);
    try {
      const order = await createOrder(productId, orderType);
      const paidFromWallet = order.status === "paid" && order.payment?.provider === "wallet";
      if (!paidFromWallet && order.payment?.payment_url) {
        window.open(order.payment.payment_url, "_blank", "noopener,noreferrer");
      }
      successLockedRef.current = true;
      setSuccessInfo(buildSuccessInfo(selectedOffer, order, orderType));
      setPurchaseStep("ready");
      await reload();
    } catch (err) {
      notify(err instanceof ApiError ? err.message : t("Не удалось создать заказ"));
    } finally {
      setOrdering(false);
    }
  };

  const openOffer = (offer: MarketOffer) => {
    successLockedRef.current = false;
    setSuccessInfo(null);
    setSelectedOffer(offer);
    setPurchaseStep("details");
    router.push(marketOfferHref(offer), { scroll: false });
  };

  const closeOffer = () => {
    const returnTab = selectedOffer?.kind === "package" ? "packages" : selectedOffer?.kind === "tokens" ? "tokens" : "programs";
    successLockedRef.current = false;
    setSuccessInfo(null);
    setSelectedOffer(null);
    setPurchaseStep("details");
    router.push(`/market/${returnTab}`, { scroll: false });
  };

  useEffect(() => {
    const match = pathname.match(/^\/market\/(programs|packages|tokens)\/([^/]+)$/);
    if (!match) {
      if (!successLockedRef.current) {
        setSelectedOffer(null);
        setPurchaseStep("details");
        setSuccessInfo(null);
      }
      return;
    }
    const [, group, slug] = match;
    if (group === "tokens") {
      const pack = apiTokens.find((item) => routeSlug(item.title) === slug || routeSlug(item.productId) === slug);
      if (pack) {
        setSelectedOffer({
          kind: "tokens",
          title: pack.title,
          price: pack.price,
          priceUsd: pack.priceUsd,
          pv: pack.pv,
          text: pack.text,
          features: pack.features,
          productId: pack.productId,
        });
        if (!successLockedRef.current) {
          setPurchaseStep("details");
          setSuccessInfo(null);
        }
      }
      return;
    }
    if (group === "packages") {
      const pack = apiPackages.find(
        (item) => routeSlug(item.title) === slug || routeSlug(item.productId) === slug,
      );
      if (pack) {
        setSelectedOffer({
          kind: "package",
          title: pack.title,
          price: pack.price,
          priceUsd: pack.priceUsd,
          pv: pack.pv,
          text: pack.text,
          features: pack.features,
          productId: pack.productId,
        });
        // После оплаты reload() обновляет tariffs — не сбрасывать экран успеха.
        if (!successLockedRef.current) {
          setPurchaseStep("details");
          setSuccessInfo(null);
        }
      }
      return;
    }
    if (!successLockedRef.current) {
      setSelectedOffer(null);
      setPurchaseStep("details");
      setSuccessInfo(null);
    }
  }, [pathname, tariffs, tokens]);

  if (!ready) {
    return (
      <PageShell>
        <PortalLoading label={t("Загрузка маркета…")} />
      </PageShell>
    );
  }

  return (
    <PageShell className={marketTab === "packages" ? "marketplace-packages-page" : "marketplace-tokens-page"}>
      {marketTab === "packages" ? (
        <>
          <header className="premium-page-intro marketplace-package-intro">
            <div>
              <span>{t("Тарифы RE:RISE")}</span>
              <h2>{t("Выберите формат старта")}</h2>
            </div>
            <p>{t("Каждый тариф активирует статус Партнёр I и первый месяц партнёрской активности. Сравните утверждённые финансовые параметры.")}</p>
          </header>
          <section className="partner-package-grid">
            {apiPackages.length === 0 ? (
              <div className="materials-empty"><strong>{t("Тарифы пока недоступны")}</strong><span>{t("Попробуйте обновить страницу чуть позже.")}</span></div>
            ) : null}
            {apiPackages.map((item) => (
              <article className={item.title === "Rise" ? "package-card rise" : item.highlight ? "package-card featured" : "package-card premium"} key={item.title}>
                <div className="package-main">
                  <span className="bundle-eyebrow">{t(item.eyebrow)}</span>
                  <h3>{item.title}</h3>
                  <p>{t(item.text)}</p>
                  <div className="bundle-gift">
                    <Sparkles size={18} />
                    <span>{t(item.note)}</span>
                  </div>
                </div>
                <div className="bundle-list">
                  {item.features.map((feature) => (
                    <div key={`${item.title}-${feature}`}>
                      <ShieldCheck size={16} />
                      <span>{t(feature)}</span>
                    </div>
                  ))}
                </div>
                <div className="bundle-buy">
                  <div className="bundle-price-line">
                    <strong>{item.price}</strong>
                  </div>
                  <button disabled={ordering} onClick={() => openOffer({
                    kind: "package",
                    title: item.title,
                    price: item.price,
                    priceUsd: item.priceUsd,
                    pv: item.pv,
                    text: item.text,
                    features: item.features,
                    productId: item.productId,
                  })}>{availableUsd >= item.priceUsd ? t("С баланса") : t("Оформить")}</button>
                </div>
              </article>
            ))}
          </section>
        </>
      ) : null}

      {marketTab === "tokens" ? (
        <>
          <header className="premium-page-intro token-page-intro">
            <div>
              <span>{t("AI Hub · RE:RISE")}</span>
              <h2>{t("Токены и использование")}</h2>
              <p>{t("Покупка AI-токенов для работы в AI Hub. Курс зависит от пакета — чем больше номинал, тем выгоднее.")}</p>
            </div>
          </header>
          <section className="token-overview">
            <article>
              <span>{t("Доступный баланс")}</span>
              <strong>{typeof home?.token_balance === "number" ? home.token_balance.toLocaleString("ru-RU") : "—"}</strong>
              <p>{t("Токены используются внутри AI Hub и не участвуют в PV, бинаре или партнёрских начислениях.")}</p>
            </article>
            <div className="token-overview-metrics">
              <div>
                <strong>{apiTokens[0]?.tokensPerUsd?.toLocaleString("ru-RU") || "—"}</strong>
                <span>{t("токенов за $1 · базовый пакет")}</span>
              </div>
              <div>
                <strong>{bestTokenRate ? bestTokenRate.toLocaleString("ru-RU") : "—"}</strong>
                <span>{t("токенов за $1 · лучший пакет")}</span>
              </div>
              <div>
                <strong>0 PV</strong>
                <span>{t("покупка токенов не даёт PV")}</span>
              </div>
            </div>
          </section>

          <section className="token-availability-card">
            {apiTokens.length === 0 ? (
              <article>
                <span className="token-availability-icon"><Zap size={22} /></span>
                <div>
                  <em>{t("Каталог")}</em>
                  <h3>{t("Пакеты токенов пока недоступны")}</h3>
                  <p>{t("Когда администратор добавит пакеты в store, они появятся здесь.")}</p>
                </div>
              </article>
            ) : null}
            {apiTokens.map((item) => (
              <article key={item.productId}>
                <span className="token-availability-icon"><Zap size={22} /></span>
                <div>
                  <em>{t("Пополнение")}</em>
                  <h3>{item.title}</h3>
                  <p>
                    {item.amount.toLocaleString("ru-RU")} {t("токенов")} · {item.price}
                    {" · "}
                    {item.tokensPerUsd.toLocaleString("ru-RU")} {t("токенов за $1")}
                  </p>
                </div>
                <div className="token-availability-action">
                  <span>{item.price}</span>
                  <button
                    disabled={ordering}
                    onClick={() => openOffer({
                      kind: "tokens",
                      title: item.title,
                      price: item.price,
                      priceUsd: item.priceUsd,
                      pv: item.pv,
                      text: item.text,
                      features: item.features,
                      productId: item.productId,
                    })}
                  >
                    {availableUsd >= item.priceUsd ? t("С баланса") : t("Купить")}
                  </button>
                </div>
              </article>
            ))}
          </section>
        </>
      ) : null}

      {selectedOffer ? (
        <PortalDialog
          title={purchaseStep === "details" ? t("Подтверждение доступа") : t("Готово")}
          eyebrow={selectedOffer.kind === "program" ? t("Программа RE:RISE") : selectedOffer.kind === "package" ? t("Пакет доступа") : t("Токены AI Hub")}
          onClose={closeOffer}
          className="purchase-dialog"
          closeLabel={t("Закрыть")}
        >
          {purchaseStep === "details" ? (
            <>
              <div className="purchase-summary">
                <div>
                  <span>{t("Вы выбрали")}</span>
                  <h3>{t(selectedOffer.title)}</h3>
                  <p>{t(selectedOffer.text)}</p>
                </div>
                <div className="purchase-price"><strong>{selectedOffer.price}</strong><span>{selectedOffer.pv}</span></div>
              </div>
              <div className="purchase-includes">
                <h4>{t("Что входит")}</h4>
                {selectedOffer.features.map((feature) => <span key={feature}><Check size={16} /> {t(feature)}</span>)}
              </div>
              {(() => {
                const priceUsd = Number(
                  selectedOffer.priceUsd
                  ?? String(selectedOffer.price).replace(/[^0-9.]/g, "")
                  ?? 0,
                );
                const canPayWallet = (
                  (selectedOffer.kind === "package" || selectedOffer.kind === "tokens")
                  && priceUsd > 0
                  && availableUsd >= priceUsd
                );
                return (
                  <>
                    <div className="marketing-plan-notice">
                      <ShieldCheck size={17} />
                      <p>{selectedOffer.kind === "package"
                        ? (() => {
                          const orderType = resolvePackageOrderType(selectedOffer.productId || "");
                          if (orderType === null) {
                            return t("Этот тариф уже активен или ниже текущего. Продление активности — через «Продлить» ($30).");
                          }
                          if (orderType === "upgrade") {
                            return canPayWallet
                              ? t(`Апгрейд с баланса ($${availableUsd.toFixed(2)}). Срок активности не сбрасывается.`)
                              : t(`Апгрейд с текущего тарифа. Баланс: $${availableUsd.toFixed(2)}. При нехватке — внешний счёт.`);
                          }
                          return canPayWallet
                            ? t(`На кошельке $${availableUsd.toFixed(2)} — хватит для оплаты с баланса. Тариф активируется сразу.`)
                            : t(`Баланс кошелька: $${availableUsd.toFixed(2)}. Если средств не хватит, будет создан внешний счёт.`);
                        })()
                        : selectedOffer.kind === "program"
                          ? t("Цена, PV, состав доступа и способ оплаты программы пока не утверждены.")
                          : (canPayWallet
                            ? t(`На кошельке $${availableUsd.toFixed(2)} — токены спишутся с баланса сразу.`)
                            : t("Пакеты токенов: при достаточном балансе USD списываются сразу. Иначе — внешний платёж. PV не начисляется."))}</p>
                    </div>
                    <footer className="portal-dialog-actions">
                      <button onClick={closeOffer}>{t("Отмена")}</button>
                      <button disabled={ordering} onClick={async () => {
                        const productId = selectedOffer.productId
                          || (selectedOffer.title === "Rise" ? "rise"
                            : selectedOffer.title === "Rise Pro" ? "rise-pro"
                            : selectedOffer.title === "Rise Pro Max" ? "rise-pro-max"
                            : "");
                        if (selectedOffer.kind === "package" || selectedOffer.kind === "tokens") {
                          if (!productId) {
                            notify(t("Не удалось определить продукт"));
                            return;
                          }
                          if (selectedOffer.kind === "package") {
                            const orderType = resolvePackageOrderType(productId);
                            if (!orderType) {
                              notify(t("Этот тариф уже у вас или ниже текущего. Для продления активности откройте «Продлить»."));
                              return;
                            }
                            await placeOrder(productId, orderType);
                            return;
                          }
                          await placeOrder(productId, "purchase");
                          return;
                        }
                        successLockedRef.current = true;
                        setSuccessInfo({
                          headline: "Заявка принята",
                          message: "Мы сообщим, когда будут утверждены цена, состав доступа и способ оплаты программы.",
                          status: "Условия в проработке",
                        });
                        setPurchaseStep("ready");
                      }}>{selectedOffer.kind === "package" || selectedOffer.kind === "tokens"
                        ? (canPayWallet
                          ? t("Оплатить с баланса")
                          : (selectedOffer.kind === "package" && currentTariffId && resolvePackageOrderType(selectedOffer.productId || "") === "upgrade"
                            ? t("Оформить апгрейд")
                            : t("Оформить заказ")))
                        : t("Уведомить о запуске")} <ChevronRight size={17} /></button>
                    </footer>
                  </>
                );
              })()}
            </>
          ) : successInfo ? (
            <PurchaseSuccessPanel info={successInfo} t={t} onDone={closeOffer} />
          ) : (
            <PurchaseSuccessPanel
              info={{
                headline: selectedOffer.title,
                message: "Операция завершена.",
                status: "Готово",
                amount: selectedOffer.kind === "package" || selectedOffer.kind === "tokens" ? selectedOffer.price : undefined,
              }}
              t={t}
              onDone={closeOffer}
            />
          )}
        </PortalDialog>
      ) : null}
    </PageShell>
  );
}
