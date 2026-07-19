"use client";

import { Lock, Play, ShoppingBag } from "lucide-react";
import type { TFn } from "../../../lib/portal";

type CourseCardData = {
  slug?: string;
  title: string;
  subtitle: string;
  progress: number;
  color: string;
  icon: React.ComponentType<{ size?: number }>;
  lessons: number;
  accessStatus?: string;
  hasAccess?: boolean;
  requiredTariff?: string | null;
};

export function CourseCard({
  course,
  onOpen,
  onUnlock,
  t,
}: {
  course: CourseCardData;
  onOpen: () => void;
  onUnlock?: () => void;
  t: TFn;
}) {
  const Icon = course.icon;
  const hasAccess = course.hasAccess !== false && course.accessStatus !== "locked";
  const isStarted = hasAccess && course.progress > 0;
  const isCompleted = hasAccess && course.progress >= 100;
  const completedLessons = Math.round((course.lessons * course.progress) / 100);
  const statusLabel = !hasAccess
    ? t("Нужен тариф")
    : isCompleted
      ? t("Завершено")
      : isStarted
        ? t("В процессе")
        : t("Доступна");

  return (
    <article className={`course-card ${course.color}${hasAccess ? "" : " program-for-sale"}`}>
      <div className="course-overlay">
        <div className="course-visual" aria-hidden="true">
          <span className="course-icon">
            <Icon size={34} />
          </span>
          <span className="course-glow" />
        </div>
        <div className={`course-topline${hasAccess ? "" : " commercial"}`}>
          <span>{course.lessons} {t("уроков")}</span>
          <em className={isCompleted ? "completed" : undefined}>
            {!hasAccess ? <><Lock size={12} /> {statusLabel}</> : statusLabel}
          </em>
        </div>
        <h3>{t(course.title)}</h3>
        <p>{t(course.subtitle)}</p>
        {hasAccess ? (
          <div className="course-bottom">
            <div
              className="progress-line"
              role="progressbar"
              aria-label={t(course.title)}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuenow={course.progress}
            >
              <span style={{ width: `${course.progress}%` }} />
            </div>
            <strong>{isStarted ? `${completedLessons} ${t("из")} ${course.lessons}` : t("Новая")}</strong>
            <button type="button" onClick={onOpen}>
              {isStarted ? t("Продолжить") : t("Открыть")}
              <Play size={15} />
            </button>
          </div>
        ) : (
          <div className="course-bottom program-purchase-bottom">
            <div className="program-card-price">
              <strong>{t("Закрыто")}</strong>
              <small>{t("Доступ после покупки партнёрского тарифа")}</small>
            </div>
            <button type="button" onClick={onUnlock ?? onOpen}>
              {t("Выбрать тариф")}
              <ShoppingBag size={15} />
            </button>
          </div>
        )}
      </div>
    </article>
  );
}
