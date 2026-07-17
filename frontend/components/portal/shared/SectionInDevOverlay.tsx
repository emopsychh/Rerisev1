"use client";

import { Construction } from "lucide-react";
import type { ReactNode } from "react";
import type { TFn } from "../../../lib/portal";

export function SectionInDevOverlay({
  t,
  description,
  children,
}: {
  t: TFn;
  title?: string;
  description: string;
  children: ReactNode;
}) {
  return (
    <div className="section-in-dev-wrap">
      <div className="section-in-dev-preview" aria-hidden="true">
        {children}
      </div>
      <div className="section-in-dev-overlay" role="status" aria-live="polite">
        <div className="section-in-dev-card">
          <span className="section-in-dev-icon compact" aria-hidden="true">
            <Construction size={22} />
          </span>
          <strong>{t("Раздел в разработке")}</strong>
          <p>{t(description)}</p>
          <em>{t("Интерфейс сохранён — подключим рабочую логику на следующем этапе.")}</em>
        </div>
      </div>
    </div>
  );
}
