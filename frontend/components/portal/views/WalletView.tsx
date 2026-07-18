"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { AlertTriangle, CalendarDays, Check, CheckCircle2, ChevronDown, ClipboardPaste, CreditCard, Filter, History, Info, Search, Send, ShieldCheck, Users, WalletCards } from "lucide-react";
import { usePortalBackend } from "../../../lib/auth/PortalBackendProvider";
import { createWithdraw, saveWalletAddress } from "../../../lib/api/wallet";
import { ApiError } from "../../../lib/api/types";
import { BINARY_RULES, WITHDRAWAL_RULES } from "../../../lib/marketing-plan";
import {
  formatLeadTime,
  formatUsd,
  hasUsdtAddress,
  maskWalletAddress,
  PAYOUT_ADDRESS_STORAGE_KEY,
} from "../../../lib/portal";
import type { NotifyFn, TFn, WalletPeriod, WalletTransactionCategory, WalletTransactionType } from "../../../lib/portal";
import { PageShell } from "../shared/PageShell";
import { PortalDialog } from "../shared/PortalDialog";
import { PortalLoading } from "../shared/PortalLoading";
import { ProgressItem } from "../shared/ProgressItem";

export function WalletView({ t, notify }: { t: TFn; notify: NotifyFn }) {
  const router = useRouter();
  const pathname = usePathname();
  const { wallet, reload, ready } = usePortalBackend();

  useEffect(() => {
    void reload();
  }, [reload]);

  const balance = wallet?.balance as { available_usd?: number; pending_usd?: number; total_earned_usd?: number } | undefined;
  const availableUsd = Number(balance?.available_usd ?? 0);
  const limits = wallet?.withdrawal_limits as { min_usd?: number; max_per_request_usd?: number } | undefined;
  const minWithdraw = Number(limits?.min_usd ?? WITHDRAWAL_RULES.minimumUsd);
  const maxWithdraw = Number(limits?.max_per_request_usd ?? Math.max(availableUsd, minWithdraw));
  const debtUsd = Number(wallet?.adjustment_debt_usd ?? 0);
  const recentApiTx = Array.isArray(wallet?.recent_transactions) ? wallet.recent_transactions as Array<Record<string, unknown>> : [];
  const mapCategory = (typeRaw: string): WalletTransactionCategory => {
    const type = typeRaw.toLowerCase();
    if (type.includes("binary")) return "binary";
    if (type.includes("match")) return "matching";
    if (type.includes("renew")) return "renewal";
    if (type.includes("fast")) return "fast_start";
    if (type.includes("withdraw")) return "withdrawal";
    if (type.includes("personal") || type.includes("direct")) return "personal";
    return "personal";
  };
  const mapTitle = (typeKey: string, direction: string, fallbackTitle: string) => {
    const type = typeKey.toLowerCase();
    if (type.includes("adjust")) {
      return direction === "debit" ? "Списание" : "Начисление";
    }
    return fallbackTitle || typeKey || "Операция";
  };
  const transactions = recentApiTx.map((tx, index) => {
    const rawAmount = Number(tx.amount_usd ?? tx.amount ?? 0);
    const direction = String(tx.direction || "").toLowerCase();
    const signed = direction === "debit" || direction === "out" ? -Math.abs(rawAmount) : Math.abs(rawAmount);
    const typeKey = String(tx.type || tx.entry_type || "");
    const createdAt = String(tx.created_at || "");
    return {
      id: String(tx.id || `TX-${index}`),
      title: mapTitle(typeKey, direction, String(tx.title || "")),
      meta: formatLeadTime(createdAt),
      amount: signed,
      date: createdAt.slice(0, 10) || new Date().toISOString().slice(0, 10),
      type: signed >= 0 ? "income" as const : "expense" as const,
      category: mapCategory(typeKey),
      status: "Завершено",
    };
  });
  const walletDialogFromPath = pathname.match(/^\/(?:finance|cabinet\/wallet)\/(withdraw|method)$/);
  const [walletDialog, setWalletDialog] = useState<"withdraw" | "method" | null>(() => (
    walletDialogFromPath?.[1] as "withdraw" | "method" | undefined
  ) ?? null);
  const [withdrawAmount, setWithdrawAmount] = useState("");
  const [payoutAddress, setPayoutAddress] = useState("");
  const [payoutAddressDraft, setPayoutAddressDraft] = useState("");
  const [rememberPayoutAddress, setRememberPayoutAddress] = useState(true);
  const [withdrawStep, setWithdrawStep] = useState<"form" | "ready">("form");
  const [walletPeriod, setWalletPeriod] = useState<WalletPeriod>("month");
  const todayIso = new Date().toISOString().slice(0, 10);
  const monthStartIso = new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().slice(0, 10);
  const [walletCustomFrom, setWalletCustomFrom] = useState(monthStartIso);
  const [walletCustomTo, setWalletCustomTo] = useState(todayIso);
  const [transactionPeriod, setTransactionPeriod] = useState<WalletPeriod>("month");
  const [transactionType, setTransactionType] = useState<WalletTransactionType>("all");
  const [transactionCustomFrom, setTransactionCustomFrom] = useState(monthStartIso);
  const [transactionCustomTo, setTransactionCustomTo] = useState(todayIso);
  const amount = Number(withdrawAmount.replace(/[^0-9.]/g, "")) || 0;
  const addressIsValid = hasUsdtAddress(payoutAddressDraft);
  const amountIsValid = amount >= minWithdraw && amount <= availableUsd && amount <= maxWithdraw;
  const canContinueWithdrawal = addressIsValid && amountIsValid;
  const openWalletDialog = (dialog: "withdraw" | "method") => {
    setPayoutAddressDraft(payoutAddress);
    setWithdrawStep("form");
    setWalletDialog(dialog);
    router.push(`/finance/${dialog}`, { scroll: false });
  };
  const closeWalletDialog = () => {
    setWalletDialog(null);
    router.push("/finance", { scroll: false });
  };

  useEffect(() => {
    const dialogMatch = pathname.match(/^\/(?:finance|cabinet\/wallet)\/(withdraw|method)$/);
    setWalletDialog((dialogMatch?.[1] as "withdraw" | "method" | undefined) ?? null);
  }, [pathname]);

  useEffect(() => {
    const savedAddress =
      (wallet?.saved_address as { address?: string } | null)?.address ||
      window.localStorage.getItem(PAYOUT_ADDRESS_STORAGE_KEY) ||
      "";
    setPayoutAddress(savedAddress);
    setPayoutAddressDraft(savedAddress);
  }, [wallet]);

  const savePayoutAddress = async (address: string) => {
    const normalizedAddress = address.trim();
    window.localStorage.setItem(PAYOUT_ADDRESS_STORAGE_KEY, normalizedAddress);
    setPayoutAddress(normalizedAddress);
    setPayoutAddressDraft(normalizedAddress);
    try {
      await saveWalletAddress({ address: normalizedAddress, network: "TRC20" });
      await reload();
    } catch {
      /* keep local draft */
    }
  };

  const pastePayoutAddress = async () => {
    try {
      const clipboardValue = await navigator.clipboard.readText();
      setPayoutAddressDraft(clipboardValue.trim());
    } catch {
      notify(t("Не удалось прочитать буфер обмена"));
    }
  };

  const periodOptions: Array<{ id: WalletPeriod; label: string }> = [
    { id: "today", label: "Сегодня" },
    { id: "yesterday", label: "Вчера" },
    { id: "week", label: "Неделя" },
    { id: "month", label: "Месяц" },
    { id: "year", label: "Год" },
    { id: "all", label: "Всё время" },
  ];
  const referenceDate = new Date();
  const matchesPeriod = (dateValue: string, period: WalletPeriod, customFrom: string, customTo: string) => {
    const date = new Date(`${dateValue}T12:00:00`);
    const startOfDay = new Date(referenceDate.getFullYear(), referenceDate.getMonth(), referenceDate.getDate());
    if (period === "all") return true;
    if (period === "custom") {
      const from = customFrom ? new Date(`${customFrom}T00:00:00`) : null;
      const to = customTo ? new Date(`${customTo}T23:59:59`) : null;
      return (!from || date >= from) && (!to || date <= to);
    }
    const toLocalIso = (value: Date) => {
      const y = value.getFullYear();
      const m = String(value.getMonth() + 1).padStart(2, "0");
      const d = String(value.getDate()).padStart(2, "0");
      return `${y}-${m}-${d}`;
    };
    if (period === "today") return dateValue === toLocalIso(startOfDay);
    if (period === "yesterday") {
      const yesterday = new Date(startOfDay);
      yesterday.setDate(yesterday.getDate() - 1);
      return dateValue === toLocalIso(yesterday);
    }
    const from = new Date(startOfDay);
    if (period === "week") from.setDate(from.getDate() - 6);
    if (period === "month") from.setDate(1);
    if (period === "year") from.setMonth(0, 1);
    return date >= from && date <= referenceDate;
  };
  const periodNotes: Record<Exclude<WalletPeriod, "custom">, string> = {
    today: "Сегодня",
    yesterday: "Вчера",
    week: "Последние 7 дней",
    month: "Текущий месяц",
    year: "Текущий год",
    all: "За всё время",
  };
  const walletPeriodTransactions = transactions.filter((item) => matchesPeriod(item.date, walletPeriod, walletCustomFrom, walletCustomTo));
  const selectedIncome = walletPeriodTransactions.filter((item) => item.amount > 0).reduce((sum, item) => sum + item.amount, 0);
  const selectedBinaryIncome = walletPeriodTransactions.filter((item) => item.category === "binary").reduce((sum, item) => sum + item.amount, 0);
  const selectedPayouts = Math.abs(walletPeriodTransactions.filter((item) => item.category === "withdrawal").reduce((sum, item) => sum + item.amount, 0));
  const formatWalletUsd = (value: number) => `$${value.toLocaleString("ru-RU", { minimumFractionDigits: Number.isInteger(value) ? 0 : 2, maximumFractionDigits: 2 })}`;
  const selectedSummary = {
    accrued: formatWalletUsd(selectedIncome),
    binary: formatWalletUsd(selectedBinaryIncome),
    debt: formatWalletUsd(debtUsd),
    paid: formatWalletUsd(selectedPayouts),
    note: walletPeriod === "custom" ? `${walletCustomFrom || "—"} — ${walletCustomTo || "—"}` : periodNotes[walletPeriod],
  };
  const bonusBreakdown = ([
    ["personal", "Личный бонус"],
    ["binary", "Бинарный бонус"],
    ["matching", "Матчинг-бонус"],
    ["renewal", "Бонус за продление"],
    ["fast_start", "Быстрый старт"],
  ] as Array<[WalletTransactionCategory, string]>).map(([category, label]) => ({
    category,
    label,
    amount: walletPeriodTransactions.filter((item) => item.category === category).reduce((sum, item) => sum + Math.max(0, item.amount), 0),
  })).filter((item) => item.amount > 0);
  const filteredTransactions = transactions.filter((item) => (
    matchesPeriod(item.date, transactionPeriod, transactionCustomFrom, transactionCustomTo)
    && (transactionType === "all" || item.type === transactionType)
  ));
  const filteredIncome = filteredTransactions.filter((item) => item.amount > 0).reduce((sum, item) => sum + item.amount, 0);
  const filteredExpense = Math.abs(filteredTransactions.filter((item) => item.amount < 0).reduce((sum, item) => sum + item.amount, 0));
  const formatAmount = (value: number) => `${value > 0 ? "+" : "−"}$${Math.abs(value).toLocaleString("ru-RU")}`;

  if (!ready) {
    return (
      <PageShell>
        <PortalLoading label={t("Загрузка финансов…")} />
      </PageShell>
    );
  }

  return (
    <PageShell>
      <section className="wallet-layout">
        <article className="wallet-hero">
          <div>
            <span>{t("Доступно к выводу")}</span>
            <strong>{formatUsd(availableUsd)}</strong>
            <p>{t("Начисления отражаются в реальном времени. Уже доступный баланс можно вывести независимо от активности подписки.")}</p>
            <div className="wallet-trust-line">
              <span><ShieldCheck size={15} /> {WITHDRAWAL_RULES.asset}</span>
              <span>{t("Минимум")} ${minWithdraw}</span>
              <span>{t("Комиссию оплачивает пользователь")}</span>
            </div>
          </div>
          <div className="wallet-actions">
            <button onClick={() => openWalletDialog("withdraw")}>{t("Вывести")}</button>
          </div>
        </article>

        <section className="wallet-period-bar" aria-label={t("Период кошелька")}>
          <div className="wallet-period-copy">
            <span><CalendarDays size={18} /></span>
            <div><strong>{t("Период отчёта")}</strong><small>{t(selectedSummary.note)}</small></div>
          </div>
          <div className="wallet-period-controls">
            <div className="wallet-period-presets">
              {periodOptions.map((option) => (
                <button
                  className={walletPeriod === option.id ? "active" : ""}
                  key={option.id}
                  onClick={() => setWalletPeriod(option.id)}
                >{t(option.label)}</button>
              ))}
              <button
                className={`wallet-calendar-button ${walletPeriod === "custom" ? "active" : ""}`}
                onClick={() => setWalletPeriod("custom")}
                aria-label={t("Выбрать даты")}
              ><CalendarDays size={17} /></button>
            </div>
            {walletPeriod === "custom" ? (
              <div className="wallet-date-range">
                <label><span>{t("С")}</span><input type="date" value={walletCustomFrom} onChange={(event) => setWalletCustomFrom(event.target.value)} /></label>
                <i>—</i>
                <label><span>{t("По")}</span><input type="date" value={walletCustomTo} onChange={(event) => setWalletCustomTo(event.target.value)} /></label>
              </div>
            ) : null}
          </div>
        </section>

        <section className="wallet-kpi-grid">
          {[
            { icon: WalletCards, label: "Начислено за период", value: selectedSummary.accrued, note: selectedSummary.note },
            { icon: Users, label: "Бинарный доход", value: selectedSummary.binary, note: `${BINARY_RULES.collapsedPvPerUsd} PV = $1` },
            { icon: AlertTriangle, label: "Корректировочный долг", value: selectedSummary.debt, note: "погашается будущими начислениями" },
            { icon: History, label: "Выведено за период", value: selectedSummary.paid, note: selectedSummary.note },
          ].map(({ icon: Icon, label, value, note }) => (
            <article className="wallet-card" key={label}>
              <span><Icon size={21} /></span>
              <p>{t(label)}</p>
              <strong>{value}</strong>
              <em>{t(note)}</em>
            </article>
          ))}
        </section>

        <article className="wallet-panel wallet-transactions">
          <div className="wallet-panel-head">
            <div>
              <h3>{t("История операций")}</h3>
              <p>{filteredTransactions.length} {t("операций")} · <b>+${filteredIncome.toLocaleString("ru-RU")}</b> · <em>−${filteredExpense.toLocaleString("ru-RU")}</em></p>
            </div>
            <span className="wallet-history-hint"><History size={15} /> {t("Прокручивается внутри")}</span>
          </div>
          <div className="wallet-history-toolbar">
            <div className="wallet-history-types" role="group" aria-label={t("Тип операции")}>
              {([
                ["all", "Все"],
                ["income", "Поступления"],
                ["expense", "Списания"],
              ] as Array<[WalletTransactionType, string]>).map(([type, label]) => (
                <button className={transactionType === type ? "active" : ""} key={type} onClick={() => setTransactionType(type)}>{t(label)}</button>
              ))}
            </div>
            <label className="wallet-history-period">
              <Filter size={15} />
              <select value={transactionPeriod} onChange={(event) => setTransactionPeriod(event.target.value as WalletPeriod)}>
                {periodOptions.map((option) => <option value={option.id} key={option.id}>{t(option.label)}</option>)}
                <option value="custom">{t("Выбрать даты")}</option>
              </select>
              <ChevronDown size={15} />
            </label>
          </div>
          {transactionPeriod === "custom" ? (
            <div className="wallet-history-custom-range wallet-date-range">
              <label><span>{t("С")}</span><input type="date" value={transactionCustomFrom} onChange={(event) => setTransactionCustomFrom(event.target.value)} /></label>
              <i>—</i>
              <label><span>{t("По")}</span><input type="date" value={transactionCustomTo} onChange={(event) => setTransactionCustomTo(event.target.value)} /></label>
            </div>
          ) : null}
          <div className="wallet-history-scroll" tabIndex={0} aria-label={t("Список операций")}>
            {filteredTransactions.length ? filteredTransactions.map((item) => (
              <div className="wallet-row" key={item.id}>
                <span className={item.type}><CreditCard size={18} /></span>
                <div>
                  <strong>{t(item.title)}</strong>
                  <p>{item.meta}</p>
                </div>
                <b className={item.type}>{formatAmount(item.amount)}</b>
                <em>{t(item.status)}</em>
              </div>
            )) : (
              <div className="wallet-history-empty">
                <Search size={24} />
                <strong>{t("Операций не найдено")}</strong>
                <p>{t("Измените период или тип операции.")}</p>
              </div>
            )}
          </div>
        </article>

        <aside className="wallet-side">
          <article className="wallet-panel wallet-payout-card">
            <div className="wallet-panel-head"><h3>{t("Условия вывода")}</h3><span>{WITHDRAWAL_RULES.asset}</span></div>
            <strong>${minWithdraw}</strong>
            <p>{t("Минимальная сумма утверждена. Сеть, точная комиссия, лимиты и срок обработки ещё определяются.")}</p>
            <div><span>{t("Комиссия")}</span><b>{t("за счёт пользователя")}</b></div>
            <div><span>{t("Режим")}</span><b>{t("автоматический · целевой")}</b></div>
          </article>
          <article className="wallet-panel">
            <div className="wallet-panel-head">
              <h3>{t("Внутренние переводы")}</h3>
              <Send size={18} />
            </div>
            <div className="marketing-plan-notice">
              <Info size={17} />
              <p>{t("Функция предусмотрена маркетинг-планом. Доступный баланс, комиссии, лимиты и возможность последующего вывода ещё не утверждены, поэтому отправка пока не включена.")}</p>
            </div>
          </article>
          <article className="wallet-panel">
            <div className="wallet-panel-head">
              <h3>{t("Реквизиты вывода")}</h3>
              <button onClick={() => openWalletDialog("method")}>{payoutAddress ? t("Изменить") : t("Добавить")}</button>
            </div>
            <div className="wallet-method wallet-method-primary">
              <ShieldCheck size={18} />
              <span><b>USDT</b><small>{t("Сеть ещё не утверждена")}</small></span>
              <small>{payoutAddress ? maskWalletAddress(payoutAddress) : t("Не указан")}</small>
            </div>
            <p className="wallet-method-note">{t("Точная сеть будет показана до сохранения финальных реквизитов и отправки средств.")}</p>
          </article>
          <article className="wallet-panel">
            <div className="wallet-panel-head">
              <h3>{t("Структура бонусов")}</h3>
            </div>
            {bonusBreakdown.map(({ label, amount }) => (
              <ProgressItem
                label={t(label)}
                value={formatWalletUsd(amount)}
                percent={selectedIncome > 0 ? Math.round((amount / selectedIncome) * 100) : 0}
                key={label}
              />
            ))}
          </article>
        </aside>
      </section>

      {walletDialog === "withdraw" || walletDialog === "method" ? (
        <PortalDialog
          title={walletDialog === "withdraw"
            ? t(withdrawStep === "ready" ? "Черновик заявки готов" : "Вывод USDT")
            : t("Адрес для выплат")}
          eyebrow={t("Кошелёк RE:RISE")}
          onClose={closeWalletDialog}
          className="withdraw-dialog"
          closeLabel={t("Закрыть")}
        >
          {withdrawStep === "ready" && walletDialog === "withdraw" ? (
            <div className="purchase-ready withdrawal-ready">
              <span><CheckCircle2 size={34} /></span>
              <h3>{t("Черновик заявки готов")}</h3>
              <p>{t("Сумма и адрес сохранены. Перед фактической отправкой портал покажет утверждённую сеть, точную комиссию и итоговую сумму к получению.")}</p>
              <div><span>{t("Сумма")}</span><strong>{amount.toLocaleString("ru-RU")} USDT</strong></div>
              <div><span>{t("Комиссия")}</span><strong>{t("За счёт пользователя · размер уточняется")}</strong></div>
              <div><span>{t("К получению")}</span><strong>{t("Будет рассчитано до отправки")}</strong></div>
              <div><span>{t("Сеть")}</span><strong>{t("Ещё не утверждена")}</strong></div>
              <div><span>{t("Адрес")}</span><strong>{maskWalletAddress(payoutAddressDraft)}</strong></div>
              <div><span>{t("Статус")}</span><strong>{t("Черновик · средства не отправлены")}</strong></div>
              <button onClick={closeWalletDialog}>{t("Готово")}</button>
            </div>
          ) : (
            <>
              <section className="withdraw-network-card">
                <span className="withdraw-asset-mark">₮</span>
                <div><small>{t("Актив вывода")}</small><strong>USDT</strong></div>
                <em><ShieldCheck size={15} /> {t("Сеть ещё не утверждена")}</em>
              </section>

              <div className="marketing-plan-notice warning">
                <AlertTriangle size={18} />
                <p>{t("Сеть и точная комиссия находятся в проработке. До их утверждения портал сохраняет реквизиты и заявку только как черновик, без отправки транзакции.")}</p>
              </div>

              <label className={`withdraw-address ${payoutAddressDraft && !addressIsValid ? "invalid" : ""}`}>
                <span>{t("Адрес USDT-кошелька")}</span>
                <div>
                  <WalletCards size={18} />
                  <input
                    value={payoutAddressDraft}
                    onChange={(event) => setPayoutAddressDraft(event.target.value.trim())}
                    placeholder={t("Вставьте адрес кошелька")}
                    autoComplete="off"
                    spellCheck={false}
                  />
                  <button type="button" onClick={pastePayoutAddress}><ClipboardPaste size={16} /> {t("Вставить")}</button>
                </div>
                <small>{payoutAddressDraft && !addressIsValid
                  ? t("Проверьте адрес: уберите пробелы и убедитесь, что он скопирован полностью.")
                  : t("Формат адреса будет окончательно проверен после утверждения сети вывода.")}</small>
              </label>

              <button
                type="button"
                className={`withdraw-remember ${rememberPayoutAddress ? "active" : ""}`}
                role="switch"
                aria-checked={rememberPayoutAddress}
                onClick={() => setRememberPayoutAddress((remember) => !remember)}
              >
                <span>{rememberPayoutAddress ? <Check size={14} /> : null}</span>
                <div><strong>{t("Сохранить адрес как черновик")}</strong><small>{t("Он подставится при следующем открытии формы и будет доступен в профиле.")}</small></div>
              </button>

              {walletDialog === "withdraw" ? (
                <>
                  <label className={`withdraw-amount withdraw-amount-wide ${withdrawAmount && !amountIsValid ? "invalid" : ""}`}>
                    <span>{t("Сумма вывода")}</span>
                    <div><b>USDT</b><input value={withdrawAmount} onChange={(event) => setWithdrawAmount(event.target.value)} inputMode="decimal" /><button onClick={() => setWithdrawAmount(String(availableUsd))}>{t("Всё")}</button></div>
                    <small>{amount > availableUsd
                      ? t("Сумма превышает доступный баланс.")
                      : `${t("Минимум")} ${minWithdraw} USDT`}</small>
                  </label>

                  <div className="withdraw-summary">
                    <div><span>{t("Доступно")}</span><strong>{availableUsd.toLocaleString("ru-RU")} USDT</strong></div>
                    <div><span>{t("Комиссия")}</span><strong>{t("Оплачивает пользователь · размер уточняется")}</strong></div>
                    <div><span>{t("К получению")}</span><strong>{t("Будет рассчитано до отправки")}</strong></div>
                    <div><span>{t("Сеть и срок")}</span><strong>{t("Будут показаны после утверждения")}</strong></div>
                  </div>

                  <div className="withdraw-warning"><AlertTriangle size={18} /><p>{t("Проверьте адрес перед подтверждением. Транзакции в блокчейне нельзя отменить после отправки.")}</p></div>
                </>
              ) : null}

              <footer className="portal-dialog-actions">
                <button onClick={closeWalletDialog}>{t("Отмена")}</button>
                <button disabled={walletDialog === "withdraw" ? !canContinueWithdrawal : !addressIsValid} onClick={() => {
                  if (!addressIsValid) return;
                  if (rememberPayoutAddress || walletDialog === "method") savePayoutAddress(payoutAddressDraft);
                  if (walletDialog === "withdraw") {
                    if (!canContinueWithdrawal) return;
                    void (async () => {
                      try {
                        await createWithdraw({
                          amount_usd: amount,
                          usdt_address: payoutAddressDraft,
                          network: "TRC20",
                        });
                        setWithdrawStep("ready");
                        await reload();
                        notify(t("Заявка на вывод отправлена"));
                      } catch (err) {
                        notify(err instanceof ApiError ? err.message : t("Не удалось создать заявку"));
                      }
                    })();
                  } else {
                    closeWalletDialog();
                    notify(t("Адрес для выплат сохранён как черновик"));
                  }
                }}>{walletDialog === "withdraw" ? t("Подготовить заявку") : t("Сохранить адрес")}</button>
              </footer>
            </>
          )}
        </PortalDialog>
      ) : null}

    </PageShell>
  );
}
