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
  const projects = [
    {
      id: "ai-landing",
      category: "design" as const,
      categoryLabel: "Дизайн",
      title: "Лендинг для AI-сервиса",
      text: "Собрать визуальную концепцию и дизайн первого экрана для запуска нового продукта.",
      budget: "$450–650",
      deadline: "4 дня",
      format: "Удалённо",
      client: "NOVA Studio",
      skills: ["Figma", "AI-визуал", "UX"],
    },
    {
      id: "reels-launch",
      category: "content" as const,
      categoryLabel: "Контент",
      title: "Серия Reels для запуска программы",
      text: "Подготовить шесть сценариев, hooks и покадровую структуру роликов для эксперта.",
      budget: "$280–360",
      deadline: "7 дней",
      format: "Удалённо",
      client: "Мария С.",
      skills: ["Reels", "Сценарии", "AI"],
    },
    {
      id: "crm-automation",
      category: "automation" as const,
      categoryLabel: "Автоматизация",
      title: "Автоматизация заявок и CRM",
      text: "Настроить путь лида от формы до задачи менеджеру и базовую цепочку сообщений.",
      budget: "$700–900",
      deadline: "10 дней",
      format: "Проект",
      client: "Growth Lab",
      skills: ["CRM", "Make", "Воронки"],
    },
    {
      id: "webinar-deck",
      category: "design" as const,
      categoryLabel: "Дизайн",
      title: "Презентация для вебинара",
      text: "Упаковать продуктовую историю в 24 слайда и подготовить визуалы для выступления.",
      budget: "$220–300",
      deadline: "3 дня",
      format: "Удалённо",
      client: "RE:RISE Partner",
      skills: ["Slides", "Storytelling", "AI"],
    },
    {
      id: "brand-content",
      category: "content" as const,
      categoryLabel: "Контент",
      title: "Контент-система личного бренда",
      text: "Собрать рубрикатор, контент-план на месяц и библиотеку промптов для команды.",
      budget: "$320–420",
      deadline: "8 дней",
      format: "Удалённо",
      client: "Артём К.",
      skills: ["Контент", "Промпты", "Стратегия"],
    },
    {
      id: "sales-flow",
      category: "automation" as const,
      categoryLabel: "Автоматизация",
      title: "AI-сценарий обработки лидов",
      text: "Спроектировать квалификацию заявок и персональные follow-up сообщения для продаж.",
      budget: "$540–720",
      deadline: "6 дней",
      format: "Проект",
      client: "Meta Sales",
      skills: ["AI Hub", "Продажи", "CRM"],
    },
  ];
  const filteredProjects = projects.filter((project) => {
    const haystack = `${project.title} ${project.text} ${project.skills.join(" ")}`.toLowerCase();
    return (filter === "all" || project.category === filter) && haystack.includes(query.toLowerCase());
  });

  return (
    <PageShell>
      <SectionInDevOverlay
        t={t}
        title="Биржа труда"
        description="Биржа труда пока не подключена к рабочей системе. Ниже сохранён будущий интерфейс — без реальных заказов и откликов."
      >
        <header className="premium-page-intro labor-intro">
          <div>
            <span>{t("Биржа RE:RISE")}</span>
            <h2>{t("Проекты внутри экосистемы")}</h2>
            <p>{t("Находите задачи по своей специализации, откликайтесь и развивайте портфолио внутри сообщества.")}</p>
          </div>
          <button className="premium-page-intro-action" type="button" tabIndex={-1}>
            <Plus size={17} />{t("Разместить портфолио")}
          </button>
        </header>

        <section className="labor-metrics" aria-label={t("Состояние биржи")}>
          {[
            ["34", "активных проекта"],
            ["128", "специалистов"],
            ["$12 480", "заказов за месяц"],
            ["4,9", "средняя оценка"],
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
          {filteredProjects.length === 0 ? (
            <div className="labor-empty"><Search size={25} /><strong>{t("Проекты не найдены")}</strong><span>{t("Измените запрос или выберите другую категорию.")}</span></div>
          ) : null}
        </section>
      </SectionInDevOverlay>
    </PageShell>
  );
}
