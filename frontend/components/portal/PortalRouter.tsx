"use client";

import { Suspense, type ReactNode } from "react";
import { usePathname } from "next/navigation";
import { PortalAppContent } from "./PortalApp";

const AUTH_PREFIXES = ["/login", "/register"];

function isAuthRoute(pathname: string) {
  return AUTH_PREFIXES.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`));
}

/**
 * Держит PortalApp смонтированным при переходах /, /courses/*, /cabinet и т.д.
 * Иначе каждый page.tsx заново монтировал приложение → вспышка «Загрузка…».
 */
export function PortalRouter({ children }: { children: ReactNode }) {
  const pathname = usePathname() || "/";

  if (isAuthRoute(pathname)) {
    return <>{children}</>;
  }

  return (
    <Suspense fallback={null}>
      <PortalAppContent />
    </Suspense>
  );
}
