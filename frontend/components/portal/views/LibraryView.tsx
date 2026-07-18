"use client";

import { useState } from "react";
import { ChevronRight, Search } from "lucide-react";
import { usePortalBackend } from "../../../lib/auth/PortalBackendProvider";
import { formatApiDate, materialsFromApi } from "../../../lib/portal";
import type { TFn } from "../../../lib/portal";
import { PageShell } from "../shared/PageShell";
import { PortalLoading } from "../shared/PortalLoading";

export function LibraryView({ openMaterial, t }: { openMaterial: (groupId: number, title: string) => void; t: TFn }) {
  const { materials, ready } = usePortalBackend();
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("Все");
  const apiMaterials = materialsFromApi(materials);
  const materialList = apiMaterials?.items ?? [];
  const categories = ["Все", ...Array.from(new Set(materialList.map((item) => item.category)))];
  const filteredMaterials = materialList.filter((item) => {
    const matchesQuery = `${item.title} ${item.text}`.toLowerCase().includes(query.toLowerCase());
    const matchesCategory = category === "Все" || item.category === category;
    return matchesQuery && matchesCategory;
  });
  const stats = apiMaterials?.stats;

  if (!ready) {
    return (
      <PageShell>
        <PortalLoading label={t("Загрузка материалов…")} />
      </PageShell>
    );
  }

  return (
    <PageShell>
      <header className="premium-page-intro materials-intro">
        <div>
          <span>{t("Рабочая база RE:RISE")}</span>
          <h2>{t("Материалы для работы")}</h2>
          <p>{t("Презентации, скрипты, шаблоны и AI-сценарии — в одной структурированной библиотеке.")}</p>
        </div>
        <div className="premium-page-intro-meta" aria-label={t("Состояние библиотеки")}>
          <span><b>{stats?.total_files ?? 0}</b>{t("файлов")}</span>
          <span><b>{stats?.total_sections ?? materialList.length}</b>{t("разделов")}</span>
          <span><b>{stats?.last_updated ? formatApiDate(stats.last_updated, t("Сегодня")) : t("Сегодня")}</b>{t("обновлено")}</span>
        </div>
      </header>

      <section className="catalog-toolbar materials-toolbar">
        <div>
          {categories.map((item) => (
            <button className={category === item ? "active" : ""} key={item} onClick={() => setCategory(item)}>{t(item)}</button>
          ))}
        </div>
        <label>
          <Search size={18} />
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder={t("Найти материал, скрипт или шаблон")} />
        </label>
        <span>{filteredMaterials.length} {t("разделов")}</span>
      </section>

      <section className="materials-grid">
        {filteredMaterials.map((item) => {
          const Icon = item.icon;
          return (
            <article className={`material-card ${item.color}`} key={item.id || item.title}>
              <div className="material-visual" aria-hidden="true">
                <span className="material-glow" />
                <span className="material-icon">
                  <Icon size={28} />
                </span>
              </div>
              <div className="material-copy">
                <span>{t(item.category)} · {item.kind} · {item.count} {t("файлов")}</span>
                <h3>{t(item.title)}</h3>
                <p>{t(item.text)}</p>
              </div>
              <div className="material-bottom">
                <small>{t("обновлено")}: {t(item.updated)}</small>
                <div className="material-actions">
                  <button type="button" onClick={() => openMaterial(item.id, item.title)}>{t("Открыть")} <ChevronRight size={18} /></button>
                </div>
              </div>
            </article>
          );
        })}
      </section>
      {filteredMaterials.length === 0 ? (
        <div className="materials-empty"><Search size={24} /><strong>{t("Ничего не найдено")}</strong><span>{t("Попробуйте изменить запрос или категорию.")}</span></div>
      ) : null}
    </PageShell>
  );
}
