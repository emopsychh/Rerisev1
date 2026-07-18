"use client";

import { BookOpen, FileText } from "lucide-react";
import type { CourseModuleItem, CrmColumn, CrmDeal } from "./types";
import { chatGptCurriculum, courseTopicSeeds, courses } from "./mock-data";
import { formatApiDate, formatLeadTime } from "./format";
import { routeSlug } from "./routing";

export function extractProgramList(programs: unknown): Array<Record<string, unknown>> {
  if (Array.isArray(programs)) return programs as Array<Record<string, unknown>>;
  if (programs && typeof programs === "object" && Array.isArray((programs as { results?: unknown[] }).results)) {
    return (programs as { results: Array<Record<string, unknown>> }).results;
  }
  return [];
}

export const emptyCrmColumns: CrmColumn[] = [
  { id: "new", title: "Новые лиды", color: "blue", deals: [] },
  { id: "contact", title: "Связаться", color: "green", deals: [] },
  { id: "meeting", title: "Встреча", color: "orange", deals: [] },
  { id: "deal", title: "Сделка", color: "violet", deals: [] },
];

export function crmColumnsFromApi(crm: unknown): CrmColumn[] | null {
  const stages = (crm as { stages?: Array<Record<string, unknown>> } | null)?.stages;
  if (!stages?.length) return null;
  return stages.map((stage) => ({
    id: String(stage.slug),
    title: String(stage.name),
    color: String(stage.color || "blue"),
    deals: (Array.isArray(stage.leads) ? stage.leads : []).map((lead) => ({
      id: String(lead.id),
      name: String(lead.name || "Новый контакт"),
      source: String(lead.source || ""),
      task: String(lead.task || ""),
      time: formatLeadTime(lead.time ?? lead.scheduled_at),
      phone: String(lead.phone || ""),
      contact: String(lead.contact || ""),
      note: String(lead.note || ""),
      email: lead.email ? String(lead.email) : undefined,
      createdAt: lead.created_at ? formatApiDate(lead.created_at, "Сегодня") : undefined,
    })),
  }));
}

export function mapApiProgramToCourse(program: Record<string, unknown>) {
  const title = String(program.title || "");
  const slug = String(program.slug || routeSlug(title));
  const mock = courses.find((course) => course.title === title || routeSlug(course.title) === slug);
  const progressObj = program.progress as { percent?: number } | null | undefined;
  return {
    slug,
    title,
    subtitle: String(program.description || ""),
    progress: Number(progressObj?.percent ?? 0),
    color: mock?.color ?? "blue",
    icon: mock?.icon ?? BookOpen,
    lessons: Number(program.lesson_count ?? 0),
  };
}

export function materialsFromApi(materials: unknown) {
  const data = materials as {
    categories?: Array<{ name: string; groups: Array<Record<string, unknown>> }>;
    stats?: { total_files?: number; total_sections?: number; last_updated?: string };
  } | null;
  if (!data?.categories?.length) return null;
  const items = data.categories.flatMap((category) =>
    category.groups.map((group) => {
      const title = String(group.title || "");
      const id = Number(group.id);
      return {
        id,
        title,
        slug: routeSlug(title),
        text: String(group.description || ""),
        count: Number(group.file_count ?? 0),
        updated: group.last_updated ? formatApiDate(group.last_updated, "—") : "—",
        category: category.name,
        kind: String(group.file_type || "DOC"),
        color: "blue",
        icon: FileText,
      };
    }),
  );
  return items.length ? { items, stats: data.stats ?? null } : null;
}

export function createNewCrmLead(id: string): CrmDeal {
  return {
    id,
    name: "Новый контакт",
    source: "Ручное добавление",
    task: "Уточнить интерес",
    time: "Сегодня",
    phone: "",
    contact: "",
    note: "",
    email: "",
    createdAt: "Сегодня",
  };
}

export function crmColumnsForRoute(_dealId?: string | null): CrmColumn[] {
  return emptyCrmColumns;
}

export function buildCourseCurriculum(course: (typeof courses)[number]): CourseModuleItem[] {
  if (course.title === "ChatGPT с нуля") return chatGptCurriculum;
  const moduleTitles = ["Старт и основа", "Инструменты и техника", "Практические сценарии", "Система работы", "Итоговый проект"];
  const topics = courseTopicSeeds[course.title] ?? ["введение", "основы", "инструменты", "практика", "сценарии", "система", "результат", "внедрение"];
  const lessonTitles = Array.from({ length: course.lessons }, (_, index) => {
    const topic = topics[index % topics.length];
    const prefixes = ["Разбираем", "Настраиваем", "Создаём", "Практика:", "Улучшаем"];
    return `${prefixes[index % prefixes.length]} ${topic}`;
  });
  let cursor = 0;
  return moduleTitles.map((title, moduleIndex) => {
    const remainingModules = moduleTitles.length - moduleIndex;
    const take = Math.ceil((lessonTitles.length - cursor) / remainingModules);
    const moduleLessons = lessonTitles.slice(cursor, cursor + take).map((title, lessonIndex) => ({
      title,
      duration: `${14 + ((cursor + lessonIndex) * 5) % 21} мин`,
    }));
    cursor += take;
    return {
      title,
      description: moduleIndex === 4 ? "Собираем итоговую работу и закрепляем процесс." : "Последовательно осваиваем тему на примерах и практике.",
      lessons: moduleLessons,
    };
  });
}
