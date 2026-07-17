"use client";

import { X } from "lucide-react";

export function PortalDialog({
  title,
  eyebrow,
  onClose,
  children,
  className = "",
  closeLabel = "Закрыть",
}: {
  title: string;
  eyebrow?: string;
  onClose: () => void;
  children: React.ReactNode;
  className?: string;
  closeLabel?: string;
}) {
  return (
    <div className="portal-dialog-backdrop" role="presentation" onClick={onClose}>
      <section
        className={`portal-dialog ${className}`}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        onClick={(event) => event.stopPropagation()}
      >
        <header className="portal-dialog-head">
          <div>
            {eyebrow ? <span>{eyebrow}</span> : null}
            <h2>{title}</h2>
          </div>
          <button onClick={onClose} aria-label={closeLabel}><X size={20} /></button>
        </header>
        {children}
      </section>
    </div>
  );
}
