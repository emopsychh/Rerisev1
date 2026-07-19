"use client";

import { useEffect, useState } from "react";
import { Copy, MessageSquareText } from "lucide-react";
import QRCode from "qrcode";
import { fetchInviteLink } from "../../../lib/api/me";
import { useAuth } from "../../../lib/auth/AuthProvider";
import { inviteUrlFromReferralCode } from "../../../lib/portal/referral";
import type { NotifyFn, TFn } from "../../../lib/portal/types";
import { PortalDialog } from "../shared/PortalDialog";

const INVITE_MESSAGE =
  "Привет! Приглашаю тебя в RE:RISE — платформу с AI-инструментами, практическим обучением и готовыми рабочими сценариями. Посмотри возможности по моей ссылке:";

export function InviteDialog({ onClose, notify, t }: { onClose: () => void; notify: NotifyFn; t: TFn }) {
  const { user } = useAuth();
  const fallback = inviteUrlFromReferralCode(user?.referral_code) || "—";
  const [inviteLink, setInviteLink] = useState(fallback);
  const [qrDataUrl, setQrDataUrl] = useState("");

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

  useEffect(() => {
    if (!inviteLink || inviteLink === "—") {
      setQrDataUrl("");
      return;
    }
    let cancelled = false;
    void QRCode.toDataURL(inviteLink, {
      width: 220,
      margin: 2,
      color: { dark: "#101414", light: "#ffffff" },
    })
      .then((url) => {
        if (!cancelled) setQrDataUrl(url);
      })
      .catch(() => {
        if (!cancelled) setQrDataUrl("");
      });
    return () => {
      cancelled = true;
    };
  }, [inviteLink]);

  const fullMessage = `${t(INVITE_MESSAGE)} ${inviteLink}`;

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
              <button type="button" onClick={() => copyValue(inviteLink, t("Ссылка скопирована"))}>
                <Copy size={17} /> {t("Скопировать")}
              </button>
            </div>
          </label>
          <button
            type="button"
            className="invite-copy-message"
            onClick={() => copyValue(fullMessage, t("Сообщение скопировано"))}
          >
            <MessageSquareText size={18} /> {t("Скопировать текст приглашения")}
          </button>
        </div>
        <aside className="invite-side">
          {qrDataUrl ? (
            <img className="invite-qr" src={qrDataUrl} alt={t("QR-код приглашения")} width={160} height={160} />
          ) : (
            <div className="invite-qr invite-qr--empty" aria-hidden />
          )}
          <strong>{t("QR-код приглашения")}</strong>
          <p>{t("Отсканируйте, чтобы открыть вашу ссылку.")}</p>
        </aside>
      </div>
    </PortalDialog>
  );
}
