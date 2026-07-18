"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { BookOpen, Check, CheckCircle2, ChevronDown, Grid2X2, Play, ShieldCheck } from "lucide-react";
import { completeLesson, fetchLesson, fetchProgram, startLesson } from "../../../lib/api/academy";
import { ApiError } from "../../../lib/api/types";
import { usePortalBackend } from "../../../lib/auth/PortalBackendProvider";
import { mapApiProgramToCourse, sectionIds } from "../../../lib/portal";
import type { NotifyFn, SectionId, TFn } from "../../../lib/portal";
import { PortalDialog } from "../shared/PortalDialog";
import { PortalLoading } from "../shared/PortalLoading";
import { ProgressItem } from "../shared/ProgressItem";

type ProgramDetail = {
  id: number;
  slug: string;
  title: string;
  description: string;
  lesson_count: number;
  module_count: number;
  progress: {
    percent: number;
    completed_lessons: number;
    status: string;
    last_lesson?: { id: number; title: string; module_title: string; duration_minutes: number } | null;
  } | null;
  modules: Array<{
    id: number;
    order: number;
    title: string;
    description: string;
    is_intro: boolean;
    lesson_count: number;
    progress: { completed_lessons: number; status: string };
    lessons: Array<{
      id: number;
      order: number;
      title: string;
      duration_minutes: number;
      type: string;
      status: string;
    }>;
  }>;
};

type LessonDetail = {
  id: number;
  title: string;
  description: string;
  result_description: string;
  type: string;
  duration_minutes: number;
  video: { url: string; quality: string } | null;
  resources: Array<{ type: string; title: string; file_url?: string | null }>;
  module: { id: number; title: string };
  progress: { status: string; video_position_sec: number };
};

function resolveMediaUrl(url: string) {
  if (/^https?:\/\//i.test(url)) return url;
  const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";
  const origin = apiBase.replace(/\/api\/v1\/?$/, "");
  return `${origin}${url.startsWith("/") ? url : `/${url}`}`;
}

// Простой кэш, чтобы при редком remount не мигал полный лоадер.
const programCache = new Map<string, ProgramDetail>();

export function CourseDetailView({
  slug,
  t,
  notify,
}: {
  slug: string;
  t: TFn;
  notify: NotifyFn;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { reload } = usePortalBackend();
  const [program, setProgram] = useState<ProgramDetail | null>(() => programCache.get(slug) ?? null);
  const [initialLoading, setInitialLoading] = useState(() => !programCache.has(slug));
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeLessonId, setActiveLessonId] = useState<number | null>(null);
  const [lessonDetail, setLessonDetail] = useState<LessonDetail | null>(null);
  const [lessonLoading, setLessonLoading] = useState(false);
  const [completing, setCompleting] = useState(false);
  const expandedInitialized = useRef(false);
  const lessonRequestId = useRef(0);

  const courseCard = useMemo(
    () => (program ? mapApiProgramToCourse(program as unknown as Record<string, unknown>) : null),
    [program],
  );
  const Icon = courseCard?.icon ?? BookOpen;
  const color = courseCard?.color ?? "blue";

  const flatLessons = useMemo(() => {
    if (!program) {
      return [] as Array<{
        id: number;
        title: string;
        duration_minutes: number;
        status: string;
        moduleIndex: number;
        moduleTitle: string;
      }>;
    }
    return program.modules.flatMap((module, moduleIndex) =>
      module.lessons.map((lesson) => ({
        id: lesson.id,
        title: lesson.title,
        duration_minutes: lesson.duration_minutes,
        status: lesson.status,
        moduleIndex,
        moduleTitle: module.title,
      })),
    );
  }, [program]);

  const progressPercent = Number(program?.progress?.percent ?? 0);
  const completedLessonCount = Number(
    program?.progress?.completed_lessons
      ?? flatLessons.filter((item) => item.status === "completed").length,
  );
  const nextLesson = flatLessons.find((item) => item.status !== "completed") ?? null;
  const isCourseCompleted = flatLessons.length > 0 && !nextLesson;
  const currentModuleIndex = nextLesson?.moduleIndex ?? Math.max(0, (program?.modules.length ?? 1) - 1);
  const [expandedModules, setExpandedModules] = useState<Set<number>>(new Set([0]));

  const parentSection = searchParams.get("from");
  const courseContextQuery = parentSection && sectionIds.has(parentSection as SectionId) ? `?from=${parentSection}` : "";
  const courseBasePath = `/courses/${slug}`;
  const coursePath = `${courseBasePath}${courseContextQuery}`;

  const activeListLesson = activeLessonId
    ? flatLessons.find((item) => item.id === activeLessonId) ?? null
    : null;
  const activeLessonIndex = activeLessonId
    ? flatLessons.findIndex((item) => item.id === activeLessonId)
    : -1;
  const lessonAfterActive = activeLessonIndex >= 0
    ? flatLessons[activeLessonIndex + 1] ?? null
    : null;
  const isActiveLessonCompleted = activeListLesson?.status === "completed";

  const loadProgram = async (mode: "initial" | "soft" = "initial") => {
    if (mode === "initial") setInitialLoading(true);
    else setRefreshing(true);
    setError(null);
    try {
      const data = await fetchProgram(slug) as ProgramDetail;
      programCache.set(slug, data);
      setProgram(data);
    } catch (err) {
      if (mode === "initial" && !programCache.has(slug)) setProgram(null);
      setError(err instanceof ApiError ? err.message : t("Не удалось загрузить программу"));
    } finally {
      setInitialLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    expandedInitialized.current = false;
    const cached = programCache.get(slug);
    if (cached) {
      setProgram(cached);
      setInitialLoading(false);
      void loadProgram("soft");
      return;
    }
    setProgram(null);
    void loadProgram("initial");
  }, [slug]);

  useEffect(() => {
    if (!program || expandedInitialized.current) return;
    setExpandedModules(new Set([currentModuleIndex]));
    expandedInitialized.current = true;
  }, [program?.slug, currentModuleIndex]);

  useEffect(() => {
    const lessonMatch = pathname.match(/^\/courses\/[^/]+\/lessons\/(\d+)$/);
    if (!lessonMatch) {
      setActiveLessonId(null);
      setLessonDetail(null);
      setLessonLoading(false);
      return;
    }
    const lessonId = Number(lessonMatch[1]);
    if (!Number.isFinite(lessonId) || lessonId <= 0) return;
    setActiveLessonId((current) => (current === lessonId ? current : lessonId));
  }, [pathname]);

  useEffect(() => {
    if (!activeLessonId) return;
    const requestId = ++lessonRequestId.current;
    let cancelled = false;
    setLessonLoading(true);
    void (async () => {
      try {
        await startLesson(activeLessonId).catch(() => null);
        const detail = await fetchLesson(activeLessonId) as LessonDetail;
        if (cancelled || requestId !== lessonRequestId.current) return;
        setLessonDetail(detail);
      } catch (err) {
        if (cancelled || requestId !== lessonRequestId.current) return;
        setLessonDetail(null);
        notify(err instanceof ApiError ? err.message : t("Не удалось открыть урок"));
        router.push(coursePath, { scroll: false });
      } finally {
        if (!cancelled && requestId === lessonRequestId.current) setLessonLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [activeLessonId]);

  const toggleModule = (moduleIndex: number) => {
    setExpandedModules((expanded) => {
      if (expanded.has(moduleIndex)) return new Set();
      return new Set([moduleIndex]);
    });
  };

  const openLessonById = (lessonId: number) => {
    if (activeLessonId !== lessonId) {
      setLessonDetail(null);
      setActiveLessonId(lessonId);
    }
    router.push(`${courseBasePath}/lessons/${lessonId}${courseContextQuery}`, { scroll: false });
  };

  const closeLesson = () => {
    lessonRequestId.current += 1;
    setActiveLessonId(null);
    setLessonDetail(null);
    setLessonLoading(false);
    router.push(coursePath, { scroll: false });
  };

  const markComplete = async () => {
    if (!activeLessonId || completing || isActiveLessonCompleted) return;
    setCompleting(true);
    try {
      await completeLesson(activeLessonId);
      notify(t("Урок отмечен как пройденный"));
      setProgram((current) => {
        if (!current) return current;
        const next = {
          ...current,
          modules: current.modules.map((module) => ({
            ...module,
            lessons: module.lessons.map((lesson) =>
              lesson.id === activeLessonId ? { ...lesson, status: "completed" } : lesson,
            ),
          })),
        };
        programCache.set(slug, next);
        return next;
      });
      void loadProgram("soft");
      void reload();
    } catch (err) {
      notify(err instanceof ApiError ? err.message : t("Не удалось завершить урок"));
    } finally {
      setCompleting(false);
    }
  };

  if (initialLoading && !program) {
    return <PortalLoading label={t("Загрузка программы…")} />;
  }

  if ((error && !program) || !program || !courseCard) {
    return (
      <section className="detail-layout">
        <div className="materials-empty">
          <strong>{error || t("Программа не найдена")}</strong>
          <span>{t("Проверьте, что курс опубликован и доступен вашему тарифу.")}</span>
        </div>
      </section>
    );
  }

  const durationLabel = (minutes: number) => `${minutes || 0} ${t("мин")}`;
  const dialogTitle = lessonDetail?.title || activeListLesson?.title || t("Урок");
  const dialogModule = lessonDetail?.module.title || activeListLesson?.moduleTitle || "";
  const showLessonPlaceholder = lessonLoading && !lessonDetail;

  return (
    <section className={`detail-layout${refreshing ? " is-refreshing" : ""}`}>
      <article className={`detail-hero ${color}`}>
        <div>
          <span className="detail-hero-eyebrow">{t("Академия RE:RISE")} · {program.lesson_count} {t("уроков")}</span>
          <h2>{t(program.title)}</h2>
          <p>{t(program.description || "")}</p>
          <div className="detail-hero-facts">
            <span><BookOpen size={15} />{program.module_count} {t("модулей")}</span>
            <span><Play size={15} />{program.lesson_count} {t("уроков")}</span>
            <span><CheckCircle2 size={15} />{progressPercent}% {t("пройдено")}</span>
          </div>
        </div>
        <div className="detail-hero-icon" aria-hidden="true">
          <Icon size={42} />
        </div>
      </article>

      <section className="detail-list-card">
        <div className="rail-title">
          <div>
            <span className="detail-module-label">{program.module_count} {t("модулей")} · {program.lesson_count} {t("уроков")}</span>
            <h3>{t("Программа курса")}</h3>
          </div>
          {isCourseCompleted ? null : (
            <button type="button" onClick={() => nextLesson && openLessonById(nextLesson.id)} disabled={!nextLesson}>
              {t("Продолжить")}
            </button>
          )}
        </div>
        <div className="course-module-list">
          {program.modules.map((module, moduleIndex) => {
            const isExpanded = expandedModules.has(moduleIndex);
            const completedInModule = module.lessons.filter((lesson) => lesson.status === "completed").length;
            const isCurrent = moduleIndex === currentModuleIndex;
            const isCompleted = module.lessons.length > 0 && completedInModule === module.lessons.length;
            return (
              <section
                className={`course-module ${isExpanded ? "expanded" : ""} ${isCurrent ? "active" : ""} ${isCompleted ? "completed" : ""}`}
                key={module.id}
              >
                <button className="course-module-head" type="button" onClick={() => toggleModule(moduleIndex)} aria-expanded={isExpanded}>
                  <span>{moduleIndex + 1}</span>
                  <div>
                    <small>
                      {t("Модуль")} {moduleIndex + 1}
                      {isCurrent ? <b>{t("Текущий модуль")}</b> : null}
                      {isCompleted ? <b>{t("Завершён")}</b> : null}
                    </small>
                    <strong>{t(module.title)}</strong>
                    <p>{t(module.description || "")}</p>
                  </div>
                  <em>{completedInModule}/{module.lessons.length}</em>
                  <ChevronDown size={19} />
                </button>
                {isExpanded ? (
                  <div className="lesson-list course-module-lessons">
                    {module.lessons.map((lesson) => {
                      const done = lesson.status === "completed";
                      const isNext = nextLesson?.id === lesson.id;
                      return (
                        <button
                          className={done ? "done" : isNext ? "current" : ""}
                          key={lesson.id}
                          type="button"
                          onClick={() => openLessonById(lesson.id)}
                        >
                          <span>{done ? <Check size={16} /> : lesson.order}</span>
                          <div>
                            <strong>{t(lesson.title)}</strong>
                            <small>
                              {durationLabel(lesson.duration_minutes)} · {done ? t("Пройден") : isNext ? t("Следующий урок") : t("Доступен")}
                            </small>
                          </div>
                          {done ? <ShieldCheck size={19} /> : <Play size={17} />}
                        </button>
                      );
                    })}
                  </div>
                ) : null}
              </section>
            );
          })}
        </div>
      </section>

      <aside className="detail-side-card course-progress-card">
        <span>{t("Ваш прогресс")}</span>
        <div className="course-progress-value">
          <strong>{progressPercent}%</strong>
          <small>{completedLessonCount} {t("из")} {flatLessons.length} {t("уроков")}</small>
        </div>
        <ProgressItem label={t("Пройдено")} value={`${completedLessonCount} / ${flatLessons.length}`} percent={progressPercent} />
        <div className="course-current-step">
          <span>{isCourseCompleted ? t("Статус курса") : t("Продолжить с места остановки")}</span>
          <strong>{t(isCourseCompleted ? "Курс пройден" : (nextLesson?.title || "—"))}</strong>
          <small>
            {isCourseCompleted
              ? t("Все уроки пройдены")
              : nextLesson
                ? `${t("Модуль")} ${nextLesson.moduleIndex + 1} · ${durationLabel(nextLesson.duration_minutes)}`
                : t("Все уроки пройдены")}
          </small>
        </div>
        {isCourseCompleted ? null : (
          <button type="button" onClick={() => nextLesson && openLessonById(nextLesson.id)} disabled={!nextLesson}>
            {t("Продолжить обучение")}
          </button>
        )}
        <div className="course-side-meta">
          <span><Grid2X2 size={15} /> {program.module_count} {t("модулей")}</span>
          <span><BookOpen size={15} /> {program.lesson_count} {t("уроков")}</span>
        </div>
      </aside>

      {activeLessonId ? (
        <PortalDialog
          title={t(dialogTitle)}
          eyebrow={`${t(program.title)}${dialogModule ? ` · ${t(dialogModule)}` : ""}`}
          onClose={closeLesson}
          className="lesson-dialog"
          closeLabel={t("Закрыть")}
        >
          <div className={`lesson-dialog-body${lessonLoading ? " is-loading" : ""}`}>
            {showLessonPlaceholder ? (
              <div className="lesson-preview-player lesson-preview-skeleton" aria-busy="true">
                <div><Play size={34} /></div>
                <span>{t("Открываем урок…")}</span>
              </div>
            ) : (
              <div className="lesson-preview-player">
                {lessonDetail?.video?.url ? (
                  <video
                    key={lessonDetail.video.url}
                    className="lesson-video"
                    controls
                    controlsList="nodownload"
                    playsInline
                    preload="metadata"
                    src={resolveMediaUrl(lessonDetail.video.url)}
                  >
                    {t("Ваш браузер не поддерживает видео")}
                  </video>
                ) : (
                  <>
                    <div><Play size={34} /></div>
                    <span>
                      {durationLabel(lessonDetail?.duration_minutes || activeListLesson?.duration_minutes || 0)}
                      {" · "}
                      {t("Видео пока не добавлено")}
                    </span>
                  </>
                )}
              </div>
            )}
            <div className="lesson-preview-copy">
              <h3>{t("Результат урока")}</h3>
              <p>
                {t(
                  lessonDetail?.result_description
                    || lessonDetail?.description
                    || "Пройдите урок и зафиксируйте результат.",
                )}
              </p>
              {lessonDetail?.resources?.length ? (
                <div>
                  {lessonDetail.resources.map((resource) => (
                    <span key={`${resource.type}-${resource.title}`}>
                      <Check size={16} /> {t(resource.title)}
                    </span>
                  ))}
                </div>
              ) : null}
            </div>
            <footer className="portal-dialog-actions">
              <button type="button" onClick={closeLesson}>{t("Вернуться к программе")}</button>
              {isActiveLessonCompleted ? (
                lessonAfterActive ? (
                  <button type="button" onClick={() => openLessonById(lessonAfterActive.id)}>
                    <Play size={17} /> {t("Следующий урок")}
                  </button>
                ) : null
              ) : (
                <button type="button" onClick={() => void markComplete()} disabled={completing || lessonLoading || !lessonDetail}>
                  <Check size={17} /> {completing ? t("Сохраняем…") : t("Отметить пройденным")}
                </button>
              )}
            </footer>
          </div>
        </PortalDialog>
      ) : null}
    </section>
  );
}
