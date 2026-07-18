"use client";

import { useEffect } from "react";
import {
  ArrowUpRight,
  ExternalLink,
  Headphones,
  Lock,
  Megaphone,
  MessageSquareText,
  Rocket,
  ShieldCheck,
  Sparkles,
  UserPlus,
  Users,
} from "lucide-react";
import { usePortalBackend } from "../../../lib/auth/PortalBackendProvider";
import type { NotifyFn, TFn } from "../../../lib/portal";
import { PageShell } from "../shared/PageShell";
import { PortalLoading } from "../shared/PortalLoading";

type ApiChat = {
  id?: number;
  title?: string;
  description?: string;
  chat_type?: string;
  telegram_url?: string | null;
  is_accessible?: boolean;
  access_requirement?: string | null;
};

const CHAT_ICON_BY_TITLE: Record<string, typeof Users> = {
  "Чат партнёров": Users,
  "Чат лидеров": Rocket,
  "Чат новичков": UserPlus,
  "Старт в RE:RISE": UserPlus,
  "Контент и AI": Sparkles,
  "Чат экспертов": Sparkles,
  "Поддержка RE:RISE": Headphones,
  "Канал маркетинга": Megaphone,
};

const CHAT_ICON_BY_TYPE: Record<string, typeof Users> = {
  open: Users,
  invite: Rocket,
  service: Headphones,
};

const CHAT_TONE_BY_TYPE: Record<string, string> = {
  open: "violet",
  invite: "orange",
  service: "green",
};

const CHAT_ACCESS_BY_TYPE: Record<string, string> = {
  open: "Открытый чат",
  invite: "По приглашению",
  service: "Сервисный чат",
};

function openChatUrl(url: string | null | undefined, title: string, notify: NotifyFn, t: TFn) {
  if (!url) {
    notify(`${t(title)} · ${t("Ссылка появится после настройки в админке")}`);
    return;
  }
  window.open(url, "_blank", "noopener,noreferrer");
}

export function ChatsView({ t, notify }: { t: TFn; notify: NotifyFn }) {
  const { chats, ready, reload } = usePortalBackend();

  useEffect(() => {
    void reload();
  }, [reload]);

  const payload = chats as {
    community_active?: boolean;
    chats?: ApiChat[];
    marketing_channel?: ApiChat | null;
  } | null;
  const apiChats = Array.isArray(payload?.chats) ? payload.chats : [];
  const marketing = payload?.marketing_channel ?? null;
  const communityActive = payload?.community_active !== false;

  if (!ready && !payload) {
    return (
      <PageShell>
        <PortalLoading label={t("Загрузка чатов…")} />
      </PageShell>
    );
  }

  return (
    <PageShell>
      <section className="news-feed chats-news-feed">
        <article className="promo-banner image-banner chats-promo-banner">
          <img className="promo-banner-image" src="/assets/portal/home-banner-partner-chat.webp" alt={t("Чат партнёров RE:RISE")} />
        </article>
        <aside className="home-ai-box-card marketing-channel-card">
          <div className="home-ai-box-icon" aria-hidden="true">
            <Megaphone size={24} />
          </div>
          <div className="home-ai-box-copy">
            <span>RE:RISE MEDIA</span>
            <h2>{t(marketing?.title || "Канал маркетинга")}</h2>
            <p>
              {t(
                marketing?.description
                  || "Готовые посты, визуалы, новости запусков и сценарии продвижения.",
              )}
            </p>
          </div>
          <button
            type="button"
            disabled={marketing?.is_accessible === false}
            onClick={() => openChatUrl(
              marketing?.is_accessible === false ? null : marketing?.telegram_url,
              marketing?.title || "Канал маркетинга",
              notify,
              t,
            )}
          >
            {marketing?.is_accessible === false
              ? t(String(marketing.access_requirement || "Недоступно"))
              : t("Открыть в Telegram")}
            <ArrowUpRight size={17} />
          </button>
        </aside>
      </section>

      <section className="community-intro">
        <div>
          <span>{t("Telegram-пространства")}</span>
          <h2>{t("Выберите чат под свою задачу")}</h2>
          <p>{t("Общий чат помогает быть внутри сообщества, а тематические пространства сохраняют фокус и скорость ответов.")}</p>
        </div>
        <div className="community-status">
          <i />
          <strong>{communityActive ? t("Сообщество активно") : t("Сообщество недоступно")}</strong>
          <span>{t("модерация и поддержка сообщества")}</span>
        </div>
      </section>

      <section className="chat-space-grid">
        {apiChats.length === 0 ? (
          <div className="materials-empty">
            <strong>{t("Чаты пока недоступны")}</strong>
            <span>{t("Добавьте Telegram-чаты в админке: Контент → Telegram-чаты.")}</span>
          </div>
        ) : null}
        {apiChats.map((chat) => {
          const title = String(chat.title || "Чат");
          const chatType = String(chat.chat_type || "open");
          const ChatIcon = CHAT_ICON_BY_TITLE[title] ?? CHAT_ICON_BY_TYPE[chatType] ?? MessageSquareText;
          const tone = CHAT_TONE_BY_TYPE[chatType] ?? "blue";
          const locked = chat.is_accessible === false;
          const access = locked && chat.access_requirement
            ? String(chat.access_requirement)
            : (CHAT_ACCESS_BY_TYPE[chatType] ?? "Открытый чат");
          const url = locked ? null : chat.telegram_url;
          return (
            <article className={`chat-space-card ${tone}${locked ? " is-locked" : ""}`} key={chat.id ?? title}>
              <header>
                <span><ChatIcon size={23} /></span>
                <em>{locked ? <><Lock size={12} /> {t(access)}</> : t(access)}</em>
              </header>
              <h2>{t(title)}</h2>
              <p>{t(String(chat.description || ""))}</p>
              <button
                type="button"
                disabled={locked || !url}
                onClick={() => openChatUrl(url, title, notify, t)}
              >
                {locked ? t("Недоступно") : t("Открыть в Telegram")}
                {locked ? <Lock size={16} /> : <ExternalLink size={16} />}
              </button>
            </article>
          );
        })}
      </section>

      <section className="community-rules">
        <strong>{t("Единый ритм сообщества")}</strong>
        {[
          [ShieldCheck, "Без спама и случайных рассылок"],
          [MessageSquareText, "Вопросы публикуются в подходящем чате"],
          [Users, "Кейсы и опыт усиливают всю сеть"],
        ].map(([RuleIcon, label]) => {
          const Icon = RuleIcon as typeof ShieldCheck;
          return <span key={label as string}><Icon size={17} />{t(label as string)}</span>;
        })}
      </section>
    </PageShell>
  );
}
