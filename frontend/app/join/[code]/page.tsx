"use client";

import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { storeReferralCode } from "../../../lib/portal/referral";
import { hasSession } from "../../../lib/api/session";

/**
 * Реферальная ссылка: /join/{CODE}
 * Новичок → сразу форма регистрации с зафиксированным кодом.
 * Уже вошёл → кабинет (код не нужен).
 */
export default function JoinReferralPage() {
  const router = useRouter();
  const params = useParams<{ code: string }>();
  const code = decodeURIComponent(String(params.code || "")).trim();

  useEffect(() => {
    if (!code) {
      router.replace("/register");
      return;
    }

    storeReferralCode(code);

    if (hasSession()) {
      router.replace("/");
      return;
    }

    router.replace(`/register?code=${encodeURIComponent(code)}`);
  }, [code, router]);

  return (
    <main className="auth-shell">
      <div className="auth-card">
        <p className="auth-brand">RE:RISE</p>
        <h1>Приглашение</h1>
        <p>Открываем регистрацию…</p>
      </div>
    </main>
  );
}
