"use client";

import { useState } from "react";
import {
  ChevronRight,
  CircleUserRound,
  Copy,
  History,
  Images,
  ListChecks,
  MessageSquareText,
  Plus,
  RefreshCw,
  Save,
  Send,
  Sparkles,
  UserPlus,
  Video,
} from "lucide-react";
import { usePortalBackend } from "../../../lib/auth/PortalBackendProvider";
import type { NotifyFn, TFn } from "../../../lib/portal";
import { PageShell } from "../shared/PageShell";
import { SectionInDevOverlay } from "../shared/SectionInDevOverlay";

export function WorkspaceView({ t, notify }: { t: TFn; notify: NotifyFn }) {
  const { home } = usePortalBackend();
  const tokenBalance = Number(home?.token_balance ?? home?.ai_box_widget?.token_balance ?? 0);
  const scenarios = [
    { title: "Пост для Telegram", prompt: "Напиши пост для Telegram о запуске новой AI-программы RE:RISE", icon: MessageSquareText },
    { title: "Сценарий Reels", prompt: "Собери сценарий Reels на тему: как AI экономит время предпринимателя", icon: Video },
    { title: "Презентация продукта", prompt: "Создай структуру презентации продукта RE:RISE для первой встречи", icon: Images },
    { title: "Сообщение для приглашения", prompt: "Напиши короткое персональное сообщение для приглашения в RE:RISE", icon: UserPlus },
    { title: "Контент-план", prompt: "Составь контент-план на 7 дней для продвижения AI-платформы", icon: ListChecks },
    { title: "AI-аватар", prompt: "Подготовь концепцию AI-аватара для эксперта в digital-продуктах", icon: CircleUserRound },
  ];
  const [model, setModel] = useState("GPT-5");
  const [prompt, setPrompt] = useState("");
  const [lastPrompt, setLastPrompt] = useState("");
  const [result, setResult] = useState({
    title: "Результат появится здесь",
    summary: "AI Hub ещё не подключён к рабочей генерации.",
    items: [] as string[],
  });
  const balance = tokenBalance;
  const [saved, setSaved] = useState(true);
  const [history, setHistory] = useState<string[]>([]);

  const runPrompt = (value = prompt) => {
    const next = value.trim();
    if (!next) {
      notify(t("Добавьте задачу для AI Hub"));
      return;
    }
    setLastPrompt(next);
    setPrompt(next);
    setResult({
      title: t("Генерация недоступна"),
      summary: t("Раздел в разработке. Токены не списываются."),
      items: [],
    });
    setSaved(false);
    setHistory((current) => [next.length > 34 ? `${next.slice(0, 34)}…` : next, ...current].slice(0, 5));
    notify(t("AI Hub пока в разработке"));
  };

  const copyResult = async () => {
    try {
      await navigator.clipboard.writeText(`${result.title}\n${result.summary}\n${result.items.join("\n")}`);
    } finally {
      notify(t("Результат скопирован"));
    }
  };

  return (
    <PageShell>
      <SectionInDevOverlay
        t={t}
        title="AI Hub"
        description="AI Hub пока не подключён к рабочей системе. Ниже сохранён будущий интерфейс — без реальных генераций и списания токенов."
      >
        <section className="workspace-shell">
          <aside className="workspace-history">
            <div className="workspace-side-head">
              <div><History size={18} /><strong>{t("История генераций")}</strong></div>
              <button type="button" tabIndex={-1} onClick={() => notify(t("Создан новый рабочий сценарий"))} aria-label={t("Новый сценарий")}>
                <Plus size={17} />
              </button>
            </div>
            <div className="workspace-balance">
              <span>{t("Баланс AI Hub")}</span>
              <strong>{balance.toLocaleString("ru-RU")}</strong>
              <small>−18 {t("за последний результат")}</small>
            </div>
            <div className="history-list">
              {history.map((item, index) => (
                <button
                  className={index === 0 ? "active" : ""}
                  key={`${item}-${index}`}
                  type="button"
                  tabIndex={-1}
                  onClick={() => {
                    const restored = item.replace("…", "");
                    setPrompt(restored);
                    setLastPrompt(restored);
                    setResult({
                      title: t("Генерация недоступна"),
                      summary: t("Раздел в разработке. Токены не списываются."),
                      items: [],
                    });
                    notify(t("Сценарий открыт"));
                  }}
                >
                  <MessageSquareText size={16} />
                  <span>{t(item)}</span>
                  <small>{index === 0 ? t("сейчас") : `${index + 1} ${t("ч")}`}</small>
                </button>
              ))}
            </div>
          </aside>

          <article className="ai-console">
            <div className="ai-console-head">
              <div className="model-tabs">
                {["GPT-5", "Claude", "Gemini"].map((item) => (
                  <button className={model === item ? "active" : ""} key={item} type="button" tabIndex={-1} onClick={() => setModel(item)}>{item}</button>
                ))}
              </div>
              <span><i />{model} {t("готов")}</span>
            </div>
            <div className="ai-conversation">
              <div className="user-message">
                <span>{t("Вы")}</span>
                <p>{t(lastPrompt)}</p>
              </div>
              <div className="assistant-result">
                <header>
                  <span><Sparkles size={18} /> {t("Последний результат")}</span>
                  <small>{model} · 18 {t("токенов")}</small>
                </header>
                <h3>{t(result.title)}</h3>
                <p>{t(result.summary)}</p>
                <div className="result-plan">
                  {result.items.map((item, index) => (
                    <div key={item}><span>{index + 1}</span><strong>{t(item)}</strong></div>
                  ))}
                </div>
                <div className="result-actions">
                  <button type="button" tabIndex={-1} onClick={copyResult}><Copy size={16} /> {t("Скопировать")}</button>
                  <button
                    type="button"
                    tabIndex={-1}
                    className={saved ? "saved" : ""}
                    onClick={() => {
                      setSaved(true);
                      notify(t("Сценарий сохранён"));
                    }}
                  >
                    <Save size={16} /> {saved ? t("Сохранено") : t("Сохранить")}
                  </button>
                  <button type="button" tabIndex={-1} onClick={() => runPrompt(lastPrompt)}><RefreshCw size={16} /> {t("Создать заново")}</button>
                </div>
              </div>
            </div>
            <div className="prompt-composer">
              <textarea value={prompt} onChange={(event) => setPrompt(event.target.value)} placeholder={t("Напишите задачу для AI Hub…")} tabIndex={-1} />
              <div>
                <button type="button" tabIndex={-1} onClick={() => notify(t("Файл добавлен к сценарию"))} aria-label={t("Добавить файл")}>
                  <Plus size={18} />
                </button>
                <span>{model} · {t("расход по результату")}</span>
                <button className="prompt-send" type="button" tabIndex={-1} onClick={() => runPrompt()} aria-label={t("Отправить")}>
                  <Send size={18} />
                </button>
              </div>
            </div>
          </article>

          <article className="tool-stack workspace-scenarios">
            <div className="workspace-side-head"><div><Sparkles size={18} /><strong>{t("Быстрые сценарии")}</strong></div></div>
            {scenarios.map(({ title, prompt: scenarioPrompt, icon: Icon }) => (
              <button key={title} type="button" tabIndex={-1} onClick={() => { setPrompt(scenarioPrompt); runPrompt(scenarioPrompt); }}>
                <Icon size={18} />{t(title)}<ChevronRight size={18} />
              </button>
            ))}
          </article>
        </section>
      </SectionInDevOverlay>
    </PageShell>
  );
}
