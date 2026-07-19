"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { usePortalBackend } from "../../../lib/auth/PortalBackendProvider";
import { extractProgramList, mapApiProgramToCourse } from "../../../lib/portal";
import type { SectionId, TFn } from "../../../lib/portal";
import { PageShell } from "../shared/PageShell";
import { PortalLoading } from "../shared/PortalLoading";
import { CourseCard } from "./CourseCard";

export function CoursesView({ openCourse, t }: { openCourse: (courseSlug: string, returnTo: SectionId, courseTitle?: string) => void; t: TFn }) {
  const router = useRouter();
  const { programs, ready } = usePortalBackend();
  const [filter, setFilter] = useState<"all" | "active" | "new" | "locked">("all");
  const courseList = extractProgramList(programs).map(mapApiProgramToCourse);
  const filteredCourses = courseList.filter((course) => {
    if (filter === "all") return true;
    if (filter === "locked") return !course.hasAccess;
    if (filter === "active") return course.hasAccess && course.progress > 0 && course.progress < 100;
    return course.hasAccess && course.progress === 0;
  });

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
          <button className={filter === "all" ? "active" : ""} type="button" onClick={() => setFilter("all")}>{t("Все")} · {courseList.length}</button>
          <button className={filter === "active" ? "active" : ""} type="button" onClick={() => setFilter("active")}>{t("В процессе")} · {courseList.filter((course) => course.hasAccess && course.progress > 0 && course.progress < 100).length}</button>
          <button className={filter === "new" ? "active" : ""} type="button" onClick={() => setFilter("new")}>{t("Доступные")} · {courseList.filter((course) => course.hasAccess && course.progress === 0).length}</button>
          <button className={filter === "locked" ? "active" : ""} type="button" onClick={() => setFilter("locked")}>{t("Закрытые")} · {courseList.filter((course) => !course.hasAccess).length}</button>
        </div>
      </section>
      <section className="course-grid full">
        {filteredCourses.map((course) => (
          <CourseCard
            course={course}
            key={course.slug}
            onOpen={() => openCourse(course.slug, "courses", course.title)}
            onUnlock={() => router.push("/market/packages")}
            t={t}
          />
        ))}
      </section>
      {filteredCourses.length === 0 ? (
        <div className="materials-empty"><strong>{t("Программы пока недоступны")}</strong><span>{t("Купите партнёрский тариф, чтобы открыть академию.")}</span></div>
      ) : null}
    </PageShell>
  );
}
