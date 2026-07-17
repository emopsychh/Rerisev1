"use client";

import { useState } from "react";
import { usePortalBackend } from "../../../lib/auth/PortalBackendProvider";
import { extractProgramList, mapApiProgramToCourse } from "../../../lib/portal";
import type { SectionId, TFn } from "../../../lib/portal";
import { PageShell } from "../shared/PageShell";
import { PortalLoading } from "../shared/PortalLoading";
import { CourseCard } from "./CourseCard";

export function CoursesView({ openCourse, t }: { openCourse: (courseSlug: string, returnTo: SectionId, courseTitle?: string) => void; t: TFn }) {
  const { programs, ready } = usePortalBackend();
  const [filter, setFilter] = useState<"all" | "active" | "new">("all");
  const courseList = extractProgramList(programs).map(mapApiProgramToCourse);
  const filteredCourses = courseList.filter((course) => filter === "all" || (filter === "active" ? course.progress > 0 : course.progress === 0));

  if (!ready) {
    return (
      <PageShell>
        <PortalLoading label={t("Загрузка академии…")} />
      </PageShell>
    );
  }

  return (
    <PageShell>
      <section className="academy-head">
        <div>
          <span>{t("Академия RE:RISE")}</span>
          <h2>{t("Обучение, которое превращается в рабочие навыки")}</h2>
          <p>{t("Продолжайте активные программы или открывайте новые направления.")}</p>
        </div>
        <div className="academy-filters">
          <button className={filter === "all" ? "active" : ""} onClick={() => setFilter("all")}>{t("Все")} · {courseList.length}</button>
          <button className={filter === "active" ? "active" : ""} onClick={() => setFilter("active")}>{t("В процессе")} · {courseList.filter((course) => course.progress > 0).length}</button>
          <button className={filter === "new" ? "active" : ""} onClick={() => setFilter("new")}>{t("Новые")} · {courseList.filter((course) => course.progress === 0).length}</button>
        </div>
      </section>
      <section className="course-grid full">
        {filteredCourses.map((course) => <CourseCard course={course} key={course.slug} onOpen={() => openCourse(course.slug, "courses", course.title)} t={t} />)}
      </section>
      {filteredCourses.length === 0 ? (
        <div className="materials-empty"><strong>{t("Программы пока недоступны")}</strong><span>{t("Попробуйте обновить страницу чуть позже.")}</span></div>
      ) : null}
    </PageShell>
  );
}
