"use client";

import { Play } from "lucide-react";
import { courses } from "../../../lib/portal";
import type { TFn } from "../../../lib/portal";

type CourseCardData = (typeof courses)[number] & { slug?: string };

export function CourseCard({ course, onOpen, t }: { course: CourseCardData; onOpen: () => void; t: TFn }) {
  const Icon = course.icon;
  const isStarted = course.progress > 0;
  const completedLessons = Math.round((course.lessons * course.progress) / 100);

  return (
    <article className={`course-card ${course.color}`}>
      <div className="course-overlay">
        <div className="course-visual" aria-hidden="true">
          <span className="course-icon">
            <Icon size={34} />
          </span>
          <span className="course-glow" />
        </div>
        <div className="course-topline">
          <span>{course.lessons} {t("уроков")}</span>
          <em>{isStarted ? t("В процессе") : t("Доступна")}</em>
        </div>
        <h3>{t(course.title)}</h3>
        <p>{t(course.subtitle)}</p>
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
            {isStarted ? t("Продолжить") : t("Посмотреть")}
            <Play size={15} />
          </button>
        </div>
      </div>
    </article>
  );
}
