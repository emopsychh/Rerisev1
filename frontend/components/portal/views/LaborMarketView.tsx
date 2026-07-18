"use client";

import { useState } from "react";
import { ChevronRight, History, MapPin, Plus, Search, ShieldCheck } from "lucide-react";
import type { NotifyFn, TFn } from "../../../lib/portal";
import { PageShell } from "../shared/PageShell";
import { SectionInDevOverlay } from "../shared/SectionInDevOverlay";

export function LaborMarketView({ t }: { t: TFn; notify?: NotifyFn }) {
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<"all" | "design" | "content" | "automation">("all");
  const filters: Array<{ id: typeof filter; label: string }> = [
    { id: "all", label: "Все проекты" },
    { id: "design", label: "Дизайн" },
    { id: "content", label: "Контент" },
    { id: "automation", label: "Автоматизация" },
  ];
  // Empty until labor API ships — no demo projects/metrics.
  const projects: Array<{
    id: string;
    category: "design" | "content" | "automation";
    categoryLabel: string;
    title: string;
    text: string;
    budget: string;
    deadline: string;
    format: string;
    client: string;
    skills: string[];
  }> = [];
  const filteredProjects = projects.filter((project) => {
    const haystack = `${project.title} ${project.text} ${project.skills.join(" ")}`.toLowerCase();
    return (filter === "all" || project.category === filter) && haystack.includes(query.toLowerCase());
  });

  return (
    <PageShell>
      <SectionInDevOverlay
        t={t}
        title="Биржа труда"
        description="Биржа труда пока не подключена. Каркас интерфейса без демонстрационных проектов и метрик."
      >
        <header className="premium-page-intro labor-intro">
          <div>
            <span>{t("Биржа RE:RISE")}</span>
            <h2>{t("Проекты внутри экосистемы")}</h2>
            <p>{t("Раздел появится после запуска биржи. Сейчас проектов нет.")}</p>
          </div>
          <button className="premium-page-intro-action" type="button" tabIndex={-1}>
            <Plus size={17} />{t("Разместить портфолио")}
          </button>
        </header>

        <section className="labor-metrics" aria-label={t("Состояние биржи")}>
          {[
            ["0", "активных проекта"],
            ["0", "специалистов"],
            ["$0", "заказов за месяц"],
            ["—", "средняя оценка"],
          ].map(([value, label]) => <div key={label}><strong>{value}</strong><span>{t(label)}</span></div>)}
        </section>

        <section className="labor-toolbar">
          <div className="labor-filter-tabs">
            {filters.map((item) => (
              <button className={filter === item.id ? "active" : ""} key={item.id} type="button" tabIndex={-1} onClick={() => setFilter(item.id)}>{t(item.label)}</button>
            ))}
          </div>
          <label>
            <Search size={18} />
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder={t("Найти проект или навык")} tabIndex={-1} />
          </label>
          <span>{filteredProjects.length} {t("проектов")}</span>
        </section>

        <section className="labor-project-grid">
          {filteredProjects.map((project) => (
            <article className={`labor-project-card ${project.category}`} key={project.id}>
              <header>
                <span>{t(project.categoryLabel)}</span>
                <b>{project.budget}</b>
              </header>
              <h2>{t(project.title)}</h2>
              <p>{t(project.text)}</p>
              <div className="labor-project-meta">
                <span><MapPin size={14} />{t(project.format)}</span>
                <span><History size={14} />{t(project.deadline)}</span>
              </div>
              <div className="labor-skill-list">{project.skills.map((skill) => <span key={skill}>{t(skill)}</span>)}</div>
              <footer>
                <div><ShieldCheck size={17} /><span>{t("Проверенный заказчик")}</span><strong>{t(project.client)}</strong></div>
                <button type="button" tabIndex={-1}>{t("Откликнуться")}<ChevronRight size={16} /></button>
              </footer>
            </article>
          ))}
          <div className="labor-empty"><Search size={25} /><strong>{t("Проекты пока не доступны")}</strong><span>{t("Биржа труда ещё не запущена.")}</span></div>
        </section>
      </SectionInDevOverlay>
    </PageShell>
  );
}
