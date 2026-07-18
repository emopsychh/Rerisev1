"use client";

import { useEffect, useRef, useState } from "react";
import type { PointerEvent as ReactPointerEvent } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { AlertTriangle, ArrowUpRight, CheckCircle2, ChevronRight, Play, Rocket, Search, Sparkles } from "lucide-react";
import { usePortalBackend } from "../../../lib/auth/PortalBackendProvider";
import {
  courses,
  extractProgramList,
  mapApiProgramToCourse,
  promoBanners,
  routeSlug,
} from "../../../lib/portal";
import type { NotifyFn, SectionId, TFn } from "../../../lib/portal";
import { PortalDialog } from "../shared/PortalDialog";
import { PortalLoading } from "../shared/PortalLoading";

type HomeBannerSlide = {
  id: string;
  title: string;
  text: string;
  image: string;
  icon: typeof Rocket;
  theme: "ai" | "academy" | "crm";
  eyebrow: string;
};

/** Local image banners for the home carousel (not from API). */
const HOME_IMAGE_BANNERS: HomeBannerSlide[] = promoBanners.slice(0, 2).map((banner, index) => ({
  id: `local-${index}`,
  title: banner.title,
  text: banner.text,
  image: banner.image,
  icon: banner.icon,
  theme: banner.theme as HomeBannerSlide["theme"],
  eyebrow: banner.eyebrow,
}));

export function HomeView({ setActive, openCourse, openAiHub, t, notify }: { setActive: (id: SectionId) => void; openCourse: (courseSlug: string, returnTo: SectionId, courseTitle?: string) => void; openAiHub: () => void; t: TFn; notify: NotifyFn }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { home, programs, ready } = usePortalBackend();
  const [activeBanner, setActiveBanner] = useState(0);
  const [courseQuery, setCourseQuery] = useState("");
  const [courseFilter, setCourseFilter] = useState<"all" | "owned" | "available" | "completed">("all");
  const [purchaseStep, setPurchaseStep] = useState<"details" | "ready">("details");
  const bannerDragStart = useRef<{ x: number; y: number; pointerId: number } | null>(null);
  const liveBanners = HOME_IMAGE_BANNERS;
  const safeBannerIndex = liveBanners.length ? activeBanner % liveBanners.length : 0;
  const banner = liveBanners[safeBannerIndex] ?? liveBanners[0];
  const isCarousel = liveBanners.length > 1;
  const courseFilters: Array<{ id: typeof courseFilter; label: string }> = [
    { id: "all", label: "Все" },
    { id: "owned", label: "Мои программы" },
    { id: "available", label: "Доступны к покупке" },
    { id: "completed", label: "Завершены" },
  ];
  const apiPrograms = extractProgramList(programs);
  const homePrograms = apiPrograms.length
    ? apiPrograms.map((program) => {
        const mapped = mapApiProgramToCourse(program);
        const accessStatus = String(program.access_status || "locked");
        const hasAccess = accessStatus !== "locked";
        return {
          title: mapped.title,
          text: mapped.subtitle,
          icon: mapped.icon,
          color: mapped.color,
          badge: Array.isArray(program.tags) && program.tags.length ? String(program.tags[0]) : undefined,
          course: mapped,
          hasAccess,
          accessStatus,
        };
      })
    : [];
  const filteredPrograms = homePrograms.filter((program) => {
    const matchesQuery = `${program.title} ${program.text}`.toLowerCase().includes(courseQuery.toLowerCase());
    const matchesFilter =
      courseFilter === "all" ||
      (courseFilter === "owned" && program.hasAccess && program.accessStatus !== "completed" && (program.course?.progress ?? 0) < 100) ||
      (courseFilter === "available" && !program.hasAccess) ||
      (courseFilter === "completed" && (program.accessStatus === "completed" || (program.hasAccess && (program.course?.progress ?? 0) >= 100)));
    return matchesQuery && matchesFilter;
  });
  const selectedProgramSlug = searchParams.get("program");
  const selectedProgram = selectedProgramSlug
    ? homePrograms.find((program) => routeSlug(program.title) === selectedProgramSlug || program.course?.slug === selectedProgramSlug) ?? null
    : null;
  const openProgramPurchase = (program: HomeProgramItem) => {
    setPurchaseStep("details");
    router.push(`/?program=${routeSlug(program.course?.slug || program.title)}`, { scroll: false });
  };
  const closeProgramPurchase = () => {
    setPurchaseStep("details");
    router.push("/", { scroll: false });
  };

  useEffect(() => {
    if (!isCarousel) return;
    const timer = window.setTimeout(() => {
      setActiveBanner((current) => (current + 1) % liveBanners.length);
    }, 5000);

    return () => window.clearTimeout(timer);
  }, [safeBannerIndex, isCarousel, liveBanners.length]);

  const moveBanner = (direction: 1 | -1) => {
    if (!isCarousel) return;
    setActiveBanner((current) => (current + direction + liveBanners.length) % liveBanners.length);
  };

  const openBanner = (index: number) => {
    setActiveBanner(index);
  };

  const handleBannerPointerDown = (event: ReactPointerEvent<HTMLElement>) => {
    if (!isCarousel) return;
    if (event.target instanceof Element && event.target.closest("button")) return;
    bannerDragStart.current = { x: event.clientX, y: event.clientY, pointerId: event.pointerId };
    event.currentTarget.setPointerCapture(event.pointerId);
  };

  const handleBannerPointerUp = (event: ReactPointerEvent<HTMLElement>) => {
    if (!isCarousel) return;
    const start = bannerDragStart.current;
    if (!start || start.pointerId !== event.pointerId) return;
    const deltaX = event.clientX - start.x;
    const deltaY = event.clientY - start.y;
    bannerDragStart.current = null;
    event.currentTarget.releasePointerCapture(event.pointerId);
    if (Math.abs(deltaX) < 64 || Math.abs(deltaX) < Math.abs(deltaY)) return;
    moveBanner(deltaX < 0 ? 1 : -1);
  };

  if (!ready) {
    return <PortalLoading label={t("Загрузка главной…")} />;
  }

  return (
    <div className="product-home">
      <section className="news-feed">
        <article
          className={`promo-banner ${banner.theme} image-banner${!isCarousel ? " is-static" : ""}`}
          aria-label={t("Баннеры")}
          onPointerDown={handleBannerPointerDown}
          onPointerUp={handleBannerPointerUp}
          onPointerCancel={() => {
            bannerDragStart.current = null;
          }}
        >
          <div className="promo-banner-slide" key={banner.id}>
            <img
              className="promo-banner-image"
              src={banner.image}
              alt={t(banner.title)}
              draggable={false}
            />
          </div>
          {isCarousel ? (
            <div className="banner-dots">
              {liveBanners.map((item, index) => (
                <button
                  className={index === safeBannerIndex ? "active" : ""}
                  key={item.id}
                  type="button"
                  onClick={() => openBanner(index)}
                  aria-label={`${t("Открыть баннер")} ${index + 1}`}
                />
              ))}
            </div>
          ) : null}
        </article>

        <aside className="home-ai-box-card">
          <div className="home-ai-box-icon" aria-hidden="true">
            <Sparkles size={24} />
          </div>
          <div className="home-ai-box-copy">
            <span>RE:RISE AI</span>
            <h2>{home?.ai_box_widget?.title || "AI Hub"}</h2>
            <p>{t(home?.ai_box_widget?.description || "AI Hub получил новые сценарии для контента и продаж")}</p>
            {typeof home?.token_balance === "number" ? (
              <small>{home.token_balance.toLocaleString("ru-RU")} {t("токенов")}</small>
            ) : null}
          </div>
          <button type="button" onClick={openAiHub} disabled={home?.ai_box_widget?.is_available === false}>
            {t("Открыть AI Hub")}
            <ArrowUpRight size={17} />
          </button>
        </aside>
      </section>

      {home?.next_action || home?.continue_learning ? (
        <section className="home-next-actions" aria-label={t("Следующий шаг")}>
          {home.next_action ? (
            <button
              type="button"
              className="home-next-card"
              onClick={() => {
                const link = home.next_action.link || "";
                if (link.includes("market") || link.includes("store")) {
                  setActive("marketplace");
                  return;
                }
                if (link.includes("crm")) {
                  setActive("crm");
                  return;
                }
                if (link.includes("wallet") || link.includes("finance")) {
                  setActive("wallet");
                  return;
                }
                if (link.includes("ibox") || link.includes("workspace") || link.includes("ai-hub") || link.includes("aihub")) {
                  openAiHub();
                  return;
                }
                if (link.includes("program") || link.includes("course") || link.includes("lesson")) {
                  if (home.continue_learning?.program_slug) {
                    openCourse(home.continue_learning.program_slug, "home", home.continue_learning.program_title);
                  } else {
                    setActive("courses");
                  }
                  return;
                }
                notify(t(home.next_action.title));
              }}
            >
              <div>
                <span>{t("Следующий шаг")}</span>
                <strong>{t(home.next_action.title)}</strong>
                <p>{t(home.next_action.subtitle)}</p>
              </div>
              <ChevronRight size={18} />
            </button>
          ) : null}
          {home.continue_learning ? (
            <button
              type="button"
              className="home-next-card continue"
              onClick={() => openCourse(home.continue_learning!.program_slug, "home", home.continue_learning!.program_title)}
            >
              <div>
                <span>{t("Продолжить обучение")}</span>
                <strong>{t(home.continue_learning.program_title)}</strong>
                <p>{t(home.continue_learning.lesson_title)} · {home.continue_learning.percent}%</p>
              </div>
              <ChevronRight size={18} />
            </button>
          ) : null}
        </section>
      ) : null}

      <section className="catalog-toolbar home-program-toolbar">
        <div>
          {courseFilters.map((item) => (
            <button className={courseFilter === item.id ? "active" : ""} key={item.id} onClick={() => setCourseFilter(item.id)}>
              {t(item.label)}
            </button>
          ))}
        </div>
        <label>
          <Search size={18} />
          <input value={courseQuery} onChange={(event) => setCourseQuery(event.target.value)} placeholder={t("Найти программу")} />
        </label>
        <span>{filteredPrograms.length} {t("программ")}</span>
      </section>

      <section className="dashboard-content">
        <section className="course-grid">
          {filteredPrograms.map((program) => (
            <HomeProgramCard
              program={program}
              key={program.title}
              onOpen={() => program.course && openCourse(program.course.slug, "home", program.course.title)}
              onBuy={() => openProgramPurchase(program)}
              t={t}
            />
          ))}
        </section>
        {filteredPrograms.length === 0 ? (
          <div className="materials-empty"><Search size={24} /><strong>{t("Программы не найдены")}</strong><span>{t("Попробуйте изменить поиск или фильтр.")}</span></div>
        ) : null}
      </section>

      {selectedProgram ? (
        <PortalDialog
          title={purchaseStep === "details" ? t("Информация о программе") : t("Запрос подготовлен")}
          eyebrow={t("Программа RE:RISE")}
          onClose={closeProgramPurchase}
          className="purchase-dialog"
          closeLabel={t("Закрыть")}
        >
          {purchaseStep === "details" ? (
            <>
              <div className="purchase-summary">
                <div><span>{t("Вы выбрали")}</span><h3>{t(selectedProgram.title)}</h3><p>{t(selectedProgram.text)}</p></div>
                <div className="purchase-price"><strong>{t("Условия уточняются")}</strong><span>{t("Продажи не открыты")}</span></div>
              </div>
              <div className="marketing-plan-notice"><AlertTriangle size={17} /><p>{t("Цена, PV и способ оплаты этой программы ещё не утверждены. Портал не будет подменять их демонстрационными значениями.")}</p></div>
              <footer className="portal-dialog-actions">
                <button onClick={closeProgramPurchase}>{t("Отмена")}</button>
                <button onClick={() => {
                  setPurchaseStep("ready");
                  notify(t("Уведомление о запуске программы включено"));
                }}>{t("Уведомить о запуске")} <ChevronRight size={17} /></button>
              </footer>
            </>
          ) : (
            <div className="purchase-ready">
              <span><CheckCircle2 size={34} /></span>
              <h3>{t(selectedProgram.title)}</h3>
              <p>{t("Мы сообщим, когда для программы будут утверждены цена, условия доступа и способ оплаты.")}</p>
              <div><span>{t("Статус")}</span><strong>{t("Условия в проработке")}</strong></div>
              <button onClick={closeProgramPurchase}>{t("Готово")}</button>
            </div>
          )}
        </PortalDialog>
      ) : null}
    </div>
  );
}

export type HomeProgramItem = {
  title: string;
  text: string;
  icon: (typeof courses)[number]["icon"];
  color: string;
  badge?: string;
  price?: string;
  pv?: string;
  course?: ReturnType<typeof mapApiProgramToCourse>;
  hasAccess: boolean;
  accessStatus?: string;
};

export function HomeProgramCard({ program, onOpen, onBuy, t }: { program: HomeProgramItem; onOpen: () => void; onBuy: () => void; t: TFn }) {
  const Icon = program.icon;
  const progress = program.course?.progress ?? 0;
  const lessons = program.course?.lessons ?? 0;
  const completedLessons = Math.round((lessons * progress) / 100);
  const hasSingleLineTitle = program.title === "Партнерские продажи";

  return (
    <article className={`course-card ${program.color} ${program.hasAccess ? "program-owned" : "program-for-sale"} ${hasSingleLineTitle ? "program-single-line-title" : ""}`}>
      <div className="course-overlay">
        <div className="course-visual" aria-hidden="true">
          <span className="course-icon"><Icon size={34} /></span>
          <span className="course-glow" />
        </div>
        {program.hasAccess ? (
          <div className="course-topline">
            <span>{lessons} {t("уроков")}</span>
            <em className={progress >= 100 ? "completed" : undefined}>{progress >= 100 ? t("Завершено") : progress > 0 ? t("В процессе") : t("Доступна")}</em>
          </div>
        ) : (
          <div className="course-topline commercial">
            <div className="course-commercial-tags">
              {program.badge ? <em>{program.badge}</em> : null}
              <span>{t("Условия доступа уточняются")}</span>
            </div>
          </div>
        )}
        <h3 className={hasSingleLineTitle ? "course-title-single-line" : undefined}>{t(program.title)}</h3>
        <p>{t(program.text)}</p>
        {program.hasAccess ? (
          <div className="course-bottom">
            <div className="progress-line" role="progressbar" aria-label={t(program.title)} aria-valuemin={0} aria-valuemax={100} aria-valuenow={progress}>
              <span style={{ width: `${progress}%` }} />
            </div>
            <strong>{completedLessons} {t("из")} {lessons}</strong>
            <button type="button" onClick={onOpen}>{progress >= 100 ? t("Открыть") : progress > 0 ? t("Продолжить") : t("Открыть")}<Play size={15} /></button>
          </div>
        ) : (
          <div className="course-bottom program-purchase-bottom">
            <div className="program-card-price"><strong>{t("Скоро")}</strong></div>
            <button type="button" onClick={onBuy}>{t("Подробнее")}<ArrowUpRight size={15} /></button>
          </div>
        )}
      </div>
    </article>
  );
}
