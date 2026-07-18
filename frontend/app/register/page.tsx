"use client";

import Link from "next/link";
import { FormEvent, Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { ApiError } from "../../lib/api/types";
import { useAuth } from "../../lib/auth/AuthProvider";
import {
  clearStoredReferralCode,
  readStoredReferralCode,
  storeReferralCode,
} from "../../lib/portal/referral";

function RegisterForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { register, user, loading } = useAuth();
  const codeFromQuery = (searchParams.get("code") || "").trim();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [referral, setReferral] = useState(codeFromQuery);
  const [referralLocked, setReferralLocked] = useState(Boolean(codeFromQuery));
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!loading && user) router.replace("/");
  }, [loading, user, router]);

  useEffect(() => {
    const fromQuery = (searchParams.get("code") || "").trim();
    if (fromQuery) {
      storeReferralCode(fromQuery);
      setReferral(fromQuery);
      setReferralLocked(true);
      return;
    }
    const stored = readStoredReferralCode();
    if (stored) {
      setReferral(stored);
      setReferralLocked(true);
    }
  }, [searchParams]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await register({
        email: email.trim(),
        password,
        first_name: firstName.trim() || undefined,
        last_name: lastName.trim() || undefined,
        referral_code: referral.trim() || undefined,
      });
      clearStoredReferralCode();
      router.replace("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось зарегистрироваться");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="auth-card" onSubmit={onSubmit}>
      <p className="auth-brand">RE:RISE</p>
      <h1>Регистрация</h1>
      <label>
        Имя
        <input value={firstName} onChange={(e) => setFirstName(e.target.value)} />
      </label>
      <label>
        Фамилия
        <input value={lastName} onChange={(e) => setLastName(e.target.value)} />
      </label>
      <label>
        Email
        <input
          type="email"
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
      </label>
      <label>
        Пароль
        <input
          type="password"
          autoComplete="new-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          minLength={8}
        />
      </label>
      <label>
        Реферальный код
        <input
          value={referral}
          onChange={(e) => setReferral(e.target.value)}
          placeholder="опционально"
          readOnly={referralLocked}
        />
      </label>
      {error ? <p className="auth-error">{error}</p> : null}
      <button type="submit" disabled={submitting}>
        {submitting ? "Создаём…" : "Создать аккаунт"}
      </button>
      <p className="auth-switch">
        Уже есть аккаунт? <Link href="/login">Войти</Link>
      </p>
    </form>
  );
}

export default function RegisterPage() {
  return (
    <main className="auth-shell">
      <Suspense fallback={<div className="auth-card"><p className="auth-brand">RE:RISE</p><h1>Регистрация</h1><p>Загрузка…</p></div>}>
        <RegisterForm />
      </Suspense>
    </main>
  );
}
