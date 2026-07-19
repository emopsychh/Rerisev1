"use client";

import { useEffect, useState } from "react";
import { Check, Copy, MessageSquareText } from "lucide-react";
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
  const [copied, setCopied] = useState<"link" | "message" | null>(null);

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
      width: 280,
      margin: 1,
      color: { dark: "#0c1212", light: "#ffffff" },
      errorCorrectionLevel: "M",
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

  const copyValue = async (value: string, kind: "link" | "message", message: string) => {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(kind);
      window.setTimeout(() => setCopied((current) => (current === kind ? null : current)), 1800);
    } finally {
      notify(message);
    }
  };

  return (
    <PortalDialog
      title={t("Пригласить в RE:RISE")}
      eyebrow={t("Партнёрская ссылка")}
      onClose={onClose}
      className="invite-dialog"
      closeLabel={t("Закрыть")}
    >
      <div className="invite-layout">
        <div className="invite-qr-block">
          <div className="invite-qr-aura" aria-hidden />
          {qrDataUrl ? (
            <img className="invite-qr" src={qrDataUrl} alt={t("QR-код приглашения")} width={168} height={168} />
          ) : (
            <div className="invite-qr invite-qr--empty" aria-hidden />
          )}
          <p>{t("Наведите камеру — откроется ваша ссылка")}</p>
        </div>

        <div className="invite-main">
          <label>
            <span>{t("Ваша персональная ссылка")}</span>
            <div className="invite-link-field">
              <strong title={inviteLink}>{inviteLink}</strong>
              <button
                type="button"
                className={copied === "link" ? "is-copied" : undefined}
                onClick={() => copyValue(inviteLink, "link", t("Ссылка скопирована"))}
              >
                {copied === "link" ? <Check size={17} /> : <Copy size={17} />}
                {copied === "link" ? t("Готово") : t("Скопировать")}
              </button>
            </div>
          </label>

          <button
            type="button"
            className={`invite-copy-message${copied === "message" ? " is-copied" : ""}`}
            onClick={() => copyValue(fullMessage, "message", t("Сообщение скопировано"))}
          >
            {copied === "message" ? <Check size={18} /> : <MessageSquareText size={18} />}
            {copied === "message" ? t("Текст скопирован") : t("Скопировать текст приглашения")}
          </button>
        </div>
      </div>
    </PortalDialog>
  );
}
