"use client";

import { useEffect, useRef, useState } from "react";
import { usePathname } from "next/navigation";
import { CalendarDays, CheckCircle2, History, ListChecks, MessageSquareText, PhoneCall, Plus, Save, Send, X } from "lucide-react";
import { usePortalBackend } from "../../../lib/auth/PortalBackendProvider";
import { createLead, updateLead } from "../../../lib/api/crm";
import { ApiError } from "../../../lib/api/types";
import { createNewCrmLead, emptyCrmColumns, crmColumnsFromApi, formatCrmPhone } from "../../../lib/portal";
import type { CrmColumn, CrmDeal, CrmTimelineNote, NotifyFn, TFn } from "../../../lib/portal";
import { PageShell } from "../shared/PageShell";
import { PortalLoading } from "../shared/PortalLoading";

export function CrmView({ t, notify }: { t: TFn; notify: NotifyFn }) {
  const pathname = usePathname();
  const { crm, reload, ready } = usePortalBackend();
  const dealFromPath = pathname.match(/^\/(?:crm|cabinet\/crm)\/deals\/([^/]+)$/);
  const [columns, setColumns] = useState<CrmColumn[]>(emptyCrmColumns);
  const [selectedDealId, setSelectedDealId] = useState<string | null>(() => dealFromPath?.[1] ?? null);
  const [draggedDealId, setDraggedDealId] = useState<string | null>(null);
  const [isDealClosing, setIsDealClosing] = useState(false);
  const [newTimelineNote, setNewTimelineNote] = useState("");
  const [timelineNotesByDeal, setTimelineNotesByDeal] = useState<Record<string, CrmTimelineNote[]>>({});
  const dealCloseTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const noteComposerRef = useRef<HTMLTextAreaElement | null>(null);
  const taskFieldRef = useRef<HTMLInputElement | null>(null);
  const [draftDeal, setDraftDeal] = useState<CrmDeal | null>(null);
  const selectedDeal = columns.flatMap((column) => column.deals).find((deal) => deal.id === selectedDealId) ?? null;
  const selectedColumn = selectedDeal ? columns.find((column) => column.deals.some((deal) => deal.id === selectedDeal.id)) : null;

  useEffect(() => {
    if (!ready) return;
    setColumns(crmColumnsFromApi(crm) ?? emptyCrmColumns);
  }, [crm, ready]);

  useEffect(() => () => {
    if (dealCloseTimer.current) clearTimeout(dealCloseTimer.current);
  }, []);

  useEffect(() => {
    const dealMatch = pathname.match(/^\/(?:crm|cabinet\/crm)\/deals\/([^/]+)$/);
    const routedDealId = dealMatch?.[1] ?? null;
    setSelectedDealId(routedDealId);
    if (routedDealId) {
      setIsDealClosing(false);
      const routedDeal = columns.flatMap((column) => column.deals).find((deal) => deal.id === routedDealId);
      if (routedDeal) setDraftDeal({
        ...routedDeal,
        email: routedDeal.email ?? "Не указан",
        createdAt: routedDeal.createdAt ?? "12 июля 2026",
      });
    }
  }, [pathname]);

  const closeDeal = () => {
    if (isDealClosing) return;
    setNewTimelineNote("");
    setIsDealClosing(true);
    if (dealCloseTimer.current) clearTimeout(dealCloseTimer.current);
    dealCloseTimer.current = setTimeout(() => {
      setSelectedDealId(null);
      setDraftDeal(null);
      setIsDealClosing(false);
      window.history.pushState(null, "", "/crm");
      dealCloseTimer.current = null;
    }, 220);
  };

  const moveDeal = (dealId: string, targetColumnId: string) => {
    setColumns((currentColumns) => {
      const dealToMove = currentColumns.flatMap((column) => column.deals).find((deal) => deal.id === dealId);
      if (!dealToMove) return currentColumns;
      return currentColumns.map((column) => {
        if (column.deals.some((deal) => deal.id === dealId)) {
          return { ...column, deals: column.deals.filter((deal) => deal.id !== dealId) };
        }
        if (column.id === targetColumnId && !column.deals.some((deal) => deal.id === dealId)) {
          return { ...column, deals: [...column.deals, dealToMove] };
        }
        return column;
      });
    });
    const numericId = Number(dealId);
    if (Number.isFinite(numericId) && numericId > 0) {
      void updateLead(numericId, { stage: targetColumnId }).then(() => reload()).catch((err) => {
        notify(err instanceof ApiError ? err.message : t("Не удалось переместить лид"));
      });
    }
  };

  const addLead = () => {
    void (async () => {
      try {
        const created = await createLead({
          name: "Новый контакт",
          source: "Вручную",
          stage: "new",
          task: "Первый контакт",
          time: "Сегодня",
          phone: "",
          contact: "",
          note: "",
        }) as Record<string, unknown>;
        await reload();
        const leadId = String(created.id || `lead-${Date.now()}`);
        const lead = createNewCrmLead(leadId);
        lead.name = String(created.name || lead.name);
        setIsDealClosing(false);
        setColumns((currentColumns) => currentColumns.map((column) => (
          column.id === "new" ? { ...column, deals: [lead, ...column.deals.filter((deal) => deal.id !== lead.id)] } : column
        )));
        setSelectedDealId(lead.id);
        setDraftDeal(lead);
        setNewTimelineNote("");
        window.history.pushState(null, "", `/crm/deals/${lead.id}`);
      } catch (err) {
        const lead = createNewCrmLead(`lead-${Date.now()}`);
        setIsDealClosing(false);
        setColumns((currentColumns) => currentColumns.map((column) => (
          column.id === "new" ? { ...column, deals: [lead, ...column.deals] } : column
        )));
        setSelectedDealId(lead.id);
        setDraftDeal(lead);
        window.history.pushState(null, "", `/crm/deals/${lead.id}`);
        notify(err instanceof ApiError ? err.message : t("Локальный черновик лида создан"));
      }
    })();
  };

  const openDeal = (deal: CrmDeal) => {
    setIsDealClosing(false);
    setSelectedDealId(deal.id);
    setNewTimelineNote("");
    setDraftDeal({
      ...deal,
      email: deal.email ?? "Не указан",
      createdAt: deal.createdAt ?? "12 июля 2026",
    });
    window.history.pushState(null, "", `/crm/deals/${deal.id}`);
  };

  const updateDealField = <K extends keyof CrmDeal>(field: K, value: CrmDeal[K]) => {
    setDraftDeal((current) => current ? { ...current, [field]: value } : current);
  };

  const saveDeal = () => {
    if (!selectedDealId || !draftDeal) return;
    setColumns((currentColumns) => currentColumns.map((column) => ({
      ...column,
      deals: column.deals.map((deal) => deal.id === selectedDealId ? { ...deal, ...draftDeal } : deal),
    })));
    const numericId = Number(selectedDealId);
    if (Number.isFinite(numericId) && numericId > 0) {
      void updateLead(numericId, {
        name: draftDeal.name,
        source: draftDeal.source,
        task: draftDeal.task,
        time: draftDeal.time,
        phone: draftDeal.phone,
        contact: draftDeal.contact,
        note: draftDeal.note,
        email: draftDeal.email,
      }).then(() => reload()).catch((err) => {
        notify(err instanceof ApiError ? err.message : t("Не удалось сохранить лид"));
      });
    }
    closeDeal();
    notify("Карточка лида сохранена");
  };

  const addTimelineNote = () => {
    const noteText = newTimelineNote.trim();
    if (!selectedDealId || !noteText) return;
    const note: CrmTimelineNote = { id: `note-${Date.now()}`, text: noteText, time: "Только что" };
    setTimelineNotesByDeal((current) => ({
      ...current,
      [selectedDealId]: [note, ...(current[selectedDealId] ?? [])],
    }));
    updateDealField("note", noteText);
    setNewTimelineNote("");
    notify("Заметка добавлена в историю");
  };

  if (!ready) {
    return (
      <PageShell>
        <PortalLoading label={t("Загрузка CRM…")} />
      </PageShell>
    );
  }

  return (
    <PageShell>
      <section className="crm-layout">
        <section className="crm-board" aria-label={t("Воронка")}>
          {columns.map((column) => (
            <article
              className={`crm-column ${column.color}`}
              key={column.id}
              onDragOver={(event) => event.preventDefault()}
              onDrop={() => {
                if (draggedDealId) moveDeal(draggedDealId, column.id);
                setDraggedDealId(null);
              }}
            >
              <header>
                <div className="crm-column-title">
                  <span>{t(column.title)}</span>
                  <b>{column.deals.length}</b>
                </div>
                {column.id === "new" ? (
                  <button type="button" onClick={addLead} aria-label={t("Добавить лид")} title={t("Добавить лид")}>
                    <Plus size={18} />
                  </button>
                ) : null}
              </header>
              <div className="crm-card-list">
                {column.deals.map((deal) => (
                  <button
                    className="crm-deal"
                    draggable
                    key={deal.id}
                    onClick={() => openDeal(deal)}
                    onDragStart={() => setDraggedDealId(deal.id)}
                    onDragEnd={() => setDraggedDealId(null)}
                  >
                    <strong>{deal.name}</strong>
                    <p>{t(deal.source)}</p>
                    <div>
                      <em>{t(deal.task)}</em>
                      <small>{t(deal.time)}</small>
                    </div>
                  </button>
                ))}
              </div>
            </article>
          ))}
        </section>
      </section>

      {selectedDeal && selectedColumn && draftDeal ? (
        <div className={`crm-modal-backdrop${isDealClosing ? " closing" : ""}`} role="presentation" onClick={closeDeal}>
          <div className="crm-drawer-shell" onClick={(event) => event.stopPropagation()}>
            <button className="crm-modal-close" onClick={closeDeal} aria-label={t("Закрыть")}><X size={20} /></button>
            <section className="crm-modal" role="dialog" aria-modal="true" aria-label={selectedDeal.name}>
            <header className="crm-modal-head">
              <div className="crm-modal-identity">
                <div>
                  <h3>{draftDeal.name}</h3>
                  <p>{t(draftDeal.source)} · {draftDeal.contact} · ID {draftDeal.id.replace("lead-", "").toUpperCase()}</p>
                </div>
              </div>
              <nav className="crm-modal-stagebar" aria-label={t("Этап сделки")}>
                {columns.map((column, columnIndex) => {
                  const selectedColumnIndex = columns.findIndex((item) => item.id === selectedColumn.id);
                  const isCurrentStage = column.id === selectedColumn.id;
                  const isReachedStage = columnIndex <= selectedColumnIndex;
                  return (
                  <button
                    type="button"
                    className={`${column.color}${isReachedStage ? " reached" : ""}${isCurrentStage ? " active" : ""}`}
                    aria-current={isCurrentStage ? "step" : undefined}
                    onClick={() => moveDeal(selectedDeal.id, column.id)}
                    key={column.id}
                  >
                    <span>{t(column.title)}</span>
                  </button>
                  );
                })}
              </nav>
            </header>

            <div className="crm-modal-body">
              <main className="crm-modal-main crm-contact-panel">
                <section className="crm-detail-section">
                  <div className="crm-section-heading"><div><span>{t("Контакт")}</span><h4>{t("Основные данные")}</h4></div></div>
                  <div className="crm-edit-grid">
                    <label className="crm-edit-field wide"><span>{t("Имя контакта")}</span><input value={draftDeal.name} onChange={(event) => updateDealField("name", event.target.value)} /></label>
                    <label className="crm-edit-field"><span>{t("Телефон")}</span><input type="tel" inputMode="tel" maxLength={18} value={formatCrmPhone(draftDeal.phone)} onChange={(event) => updateDealField("phone", formatCrmPhone(event.target.value))} /></label>
                    <label className="crm-edit-field"><span>Telegram</span><input value={draftDeal.contact} onChange={(event) => updateDealField("contact", event.target.value)} /></label>
                    <label className="crm-edit-field"><span>Email</span><input value={draftDeal.email} onChange={(event) => updateDealField("email", event.target.value)} /></label>
                    <label className="crm-edit-field"><span>{t("Источник")}</span><input value={draftDeal.source} onChange={(event) => updateDealField("source", event.target.value)} /></label>
                  </div>
                </section>

                <section className="crm-detail-section">
                  <div className="crm-section-heading"><div><span>{t("Сделка")}</span><h4>{t("Следующий шаг")}</h4></div></div>
                  <div className="crm-next-action">
                    <label className="crm-edit-field"><span>{t("Действие")}</span><input ref={taskFieldRef} value={draftDeal.task} onChange={(event) => updateDealField("task", event.target.value)} /></label>
                    <label className="crm-edit-field"><span>{t("Срок")}</span><input value={draftDeal.time} onChange={(event) => updateDealField("time", event.target.value)} /></label>
                  </div>
                </section>
              </main>

              <aside className="crm-modal-side crm-timeline-panel">
                <section className="crm-side-card crm-quick-actions-card">
                  <div className="crm-section-heading"><div><span>{t("Действия")}</span><h4>{t("Работа с лидом")}</h4></div></div>
                  <div className="crm-modal-actions">
                    <button onClick={() => notify(`Звонок для ${draftDeal.name} добавлен в план`)}><PhoneCall size={16} /><span>{t("Позвонить")}</span></button>
                    <button onClick={() => notify(`Сообщение для ${draftDeal.name} подготовлено`)}><Send size={16} /><span>{t("Написать")}</span></button>
                    <button onClick={() => notify(`Встреча с ${draftDeal.name} запланирована`)}><CalendarDays size={16} /><span>{t("Встреча")}</span></button>
                    <button onClick={() => noteComposerRef.current?.focus()}><MessageSquareText size={16} /><span>{t("Заметка")}</span></button>
                    <button onClick={() => taskFieldRef.current?.focus()}><ListChecks size={16} /><span>{t("Задача")}</span></button>
                  </div>
                </section>

                <section className="crm-side-card crm-note-composer">
                  <div className="crm-section-heading"><div><span>{t("Активность")}</span><h4>{t("Новая заметка")}</h4></div><MessageSquareText size={15} /></div>
                  <textarea ref={noteComposerRef} value={newTimelineNote} onChange={(event) => setNewTimelineNote(event.target.value)} placeholder={t("Зафиксируйте итоги разговора, договорённости или следующий шаг")} />
                  <footer>
                    <small>{t("Заметка появится в истории лида")}</small>
                    <button type="button" disabled={!newTimelineNote.trim()} onClick={addTimelineNote}><Plus size={15} />{t("Добавить заметку")}</button>
                  </footer>
                </section>

                <section className="crm-side-card crm-timeline-card">
                  <div className="crm-section-heading"><div><span>{t("История")}</span><h4>{t("Хронология взаимодействий")}</h4></div><History size={15} /></div>
                  <div className="crm-timeline-list">
                    {(timelineNotesByDeal[selectedDeal.id] ?? []).map((note) => (
                      <article className="crm-timeline-event note" key={note.id}>
                        <i><MessageSquareText size={15} /></i>
                        <div><header><strong>{t("Добавлена заметка")}</strong><time>{t(note.time)}</time></header><p>{note.text}</p></div>
                      </article>
                    ))}
                    <article className="crm-timeline-event note">
                      <i><MessageSquareText size={15} /></i>
                      <div><header><strong>{t("Добавлена заметка")}</strong><time>{t("Сегодня, 12:40")}</time></header><p>{t(selectedDeal.note)}</p></div>
                    </article>
                    <article className="crm-timeline-event call">
                      <i><PhoneCall size={15} /></i>
                      <div><header><strong>{t("Первичный контакт")}</strong><time>{t("Сегодня, 11:15")}</time></header><p>{t("Лид квалифицирован, зафиксирован следующий шаг")}</p></div>
                    </article>
                    <article className="crm-timeline-event created">
                      <i><Plus size={15} /></i>
                      <div><header><strong>{t("Лид создан")}</strong><time>{draftDeal.createdAt}</time></header><p>{t(draftDeal.source)}</p></div>
                    </article>
                  </div>
                </section>
              </aside>
            </div>

            <footer className="crm-modal-footer">
              <span><CheckCircle2 size={15} /> {t("Изменения сохранятся в карточке лида")}</span>
              <div><button type="button" onClick={closeDeal}>{t("Отмена")}</button><button onClick={saveDeal}><Save size={16} />{t("Сохранить изменения")}</button></div>
            </footer>
            </section>
          </div>
        </div>
      ) : null}
    </PageShell>
  );
}
