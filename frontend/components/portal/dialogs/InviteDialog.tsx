"use client";

import { useEffect, useState } from "react";
import { Copy, MessageSquareText, QrCode, Send } from "lucide-react";
import { fetchInviteLink } from "../../../lib/api/me";
import { useAuth } from "../../../lib/auth/AuthProvider";
import { inviteUrlFromReferralCode } from "../../../lib/portal/referral";
import type { NotifyFn, TFn } from "../../../lib/portal/types";
import { PortalDialog } from "../shared/PortalDialog";

export function InviteDialog({ onClose, notify, t }: { onClose: () => void; notify: NotifyFn; t: TFn }) {
  const { user } = useAuth();
  const fallback = inviteUrlFromReferralCode(user?.referral_code) || "—";
  const [inviteLink, setInviteLink] = useState(fallback);
  const inviteMessage = "Привет! Приглашаю тебя в RE:RISE — платформу с AI-инструментами, практическим обучением и готовыми рабочими сценариями. Посмотри возможности по моей ссылке:";

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const data = await fetchInviteLink();
        if (!cancelled && data.invite_url) setInviteLink(data.invite_url);
      } catch {
        if (!cancelled) setInviteLink(fallback);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [fallback]);

  const copyValue = async (value: string, message: string) => {
    try {
      await navigator.clipboard.writeText(value);
    } finally {
      notify(message);
    }
  };

  return (
    <PortalDialog title={t("Пригласить в RE:RISE")} eyebrow={t("Партнёрская ссылка")} onClose={onClose} className="invite-dialog" closeLabel={t("Закрыть")}>
      <div className="invite-dialog-grid">
        <div className="invite-main">
          <label>
            <span>{t("Ваша персональная ссылка")}</span>
            <div className="invite-link-field">
              <strong>{inviteLink}</strong>
              <button onClick={() => copyValue(inviteLink, t("Ссылка скопирована"))}><Copy size={17} /> {t("Скопировать")}</button>
            </div>
          </label>
          <label>
            <span>{t("Сообщение для приглашения")}</span>
            <textarea readOnly value={`${t(inviteMessage)} ${inviteLink}`} />
          </label>
          <div className="invite-actions">
            <button onClick={() => copyValue(`${t(inviteMessage)} ${inviteLink}`, t("Сообщение скопировано"))}>
              <MessageSquareText size={18} /> {t("Скопировать сообщение")}
            </button>
            <button onClick={() => notify(t("Ссылка подготовлена для отправки в Telegram"))}>
              <Send size={18} /> {t("Отправить")}
            </button>
          </div>
        </div>
        <aside className="invite-side">
          <div className="qr-placeholder" aria-label={t("QR-код приглашения")}>
            <QrCode size={92} />
          </div>
          <strong>{t("QR-код приглашения")}</strong>
          <p>{t("Подходит для презентаций, встреч и печатных материалов.")}</p>
          <div className="invite-stats">
            <div><span>{t("Переходы")}</span><b>—</b></div>
            <div><span>{t("Регистрации")}</span><b>—</b></div>
            <div><span>{t("Конверсия")}</span><b>—</b></div>
          </div>
        </aside>
      </div>
    </PortalDialog>
  );
}
