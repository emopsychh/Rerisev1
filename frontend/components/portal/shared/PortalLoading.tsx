"use client";

export function PortalLoading({ label = "Загрузка…" }: { label?: string }) {
  return (
    <div className="portal-section-loading" role="status" aria-live="polite">
      <span className="portal-section-loading-dot" aria-hidden="true" />
      <p>{label}</p>
    </div>
  );
}
