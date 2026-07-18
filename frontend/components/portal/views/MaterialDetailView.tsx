"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { ChevronRight, Download, FileText, Sparkles } from "lucide-react";
import { fetchMaterialGroup } from "../../../lib/api/content";
import { getApiBaseUrl } from "../../../lib/api/client";
import { getAccessToken } from "../../../lib/api/session";
import { ApiError } from "../../../lib/api/types";
import { routeSlug } from "../../../lib/portal";
import type { NotifyFn, TFn } from "../../../lib/portal";
import { PortalDialog } from "../shared/PortalDialog";
import { PortalLoading } from "../shared/PortalLoading";

export type MaterialSummary = {
  id: number;
  title: string;
  text: string;
  count: number;
  updated: string;
  category: string;
  color?: string;
  icon?: typeof FileText;
};

type MaterialFileRow = {
  id: number;
  title: string;
  format: string;
  file_url: string;
  file_size: number;
};

async function openMaterialDownload(file: MaterialFileRow, notify: NotifyFn, t: TFn) {
  if (file.file_url && /^https?:\/\//i.test(file.file_url)) {
    window.open(file.file_url, "_blank", "noopener,noreferrer");
    return;
  }
  try {
    const token = getAccessToken();
    const response = await fetch(`${getApiBaseUrl()}/materials/files/${file.id}/download`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      redirect: "follow",
    });
    if (!response.ok) {
      notify(t("Не удалось скачать файл"));
      return;
    }
    const blob = await response.blob();
    const objectUrl = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = objectUrl;
    link.download = file.title || `file-${file.id}`;
    link.click();
    URL.revokeObjectURL(objectUrl);
  } catch {
    notify(t("Не удалось скачать файл"));
  }
}

export function MaterialDetailView({
  material,
  t,
  notify,
  openAiHub,
}: {
  material: MaterialSummary;
  t: TFn;
  notify: NotifyFn;
  openAiHub: () => void;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const Icon = material.icon ?? FileText;
  const [files, setFiles] = useState<MaterialFileRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const materialPath = `/materials/${material.id}-${routeSlug(material.title)}`;
  const fileFromPath = pathname.match(/^\/materials\/[^/]+\/files\/(\d+)$/);
  const [selectedFileId, setSelectedFileId] = useState<number | null>(() => {
    const fileId = fileFromPath ? Number(fileFromPath[1]) : NaN;
    return Number.isFinite(fileId) ? fileId : null;
  });
  const selectedFile = files.find((file) => file.id === selectedFileId) ?? null;

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setLoadError(null);
    void fetchMaterialGroup(material.id)
      .then((detail) => {
        if (cancelled) return;
        setFiles(Array.isArray(detail.files) ? detail.files : []);
      })
      .catch((error) => {
        if (cancelled) return;
        setFiles([]);
        setLoadError(error instanceof ApiError ? error.message : t("Не удалось загрузить файлы"));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [material.id, t]);

  useEffect(() => {
    const fileMatch = pathname.match(/^\/materials\/[^/]+\/files\/(\d+)$/);
    const fileId = fileMatch ? Number(fileMatch[1]) : NaN;
    setSelectedFileId(Number.isFinite(fileId) ? fileId : null);
  }, [pathname]);

  const openFile = (fileId: number) => {
    setSelectedFileId(fileId);
    router.push(`${materialPath}/files/${fileId}`, { scroll: false });
  };
  const closeFile = () => {
    setSelectedFileId(null);
    router.push(materialPath, { scroll: false });
  };

  return (
    <section className="detail-layout">
      <article className={`detail-hero ${material.color || "blue"}`}>
        <div>
          <span>{material.count} {t("файлов")}</span>
          <h2>{t(material.title)}</h2>
          <p>{t(material.text || "—")}</p>
        </div>
        <div className="detail-hero-icon" aria-hidden="true">
          <Icon size={42} />
        </div>
      </article>

      <section className="detail-list-card">
        <div className="rail-title">
          <h3>{t("Файлы и шаблоны")}</h3>
          <button
            type="button"
            disabled={!files.length}
            onClick={() => {
              if (!files.length) return;
              void openMaterialDownload(files[0], notify, t);
              if (files.length > 1) notify(t("Открыт первый файл. Остальные доступны в списке."));
            }}
          >
            <Download size={16} /> {t("Скачать")}
          </button>
        </div>
        {loading ? <PortalLoading label={t("Загрузка файлов…")} /> : null}
        {loadError ? <div className="materials-empty"><strong>{loadError}</strong></div> : null}
        {!loading && !loadError && files.length === 0 ? (
          <div className="materials-empty"><strong>{t("Файлы пока не добавлены")}</strong></div>
        ) : null}
        <div className="material-file-list">
          {files.map((file) => (
            <button type="button" key={file.id} onClick={() => openFile(file.id)}>
              <span>{file.format || "FILE"}</span>
              <div>
                <strong>{t(file.title)}</strong>
                <small>{t("обновлено")}: {t(material.updated)}</small>
              </div>
              <ChevronRight size={20} />
            </button>
          ))}
        </div>
      </section>

      <aside className="detail-side-card">
        <span>{t("Раздел")}</span>
        <strong>{files.length || material.count}</strong>
        <p>{t(material.category || "Материалы")}</p>
        <button type="button" onClick={openAiHub}>{t("Открыть в AI Hub")}</button>
      </aside>

      {selectedFile ? (
        <PortalDialog title={t(selectedFile.title)} eyebrow={`${t(material.title)} · ${selectedFile.format || "FILE"}`} onClose={closeFile} className="material-preview-dialog" closeLabel={t("Закрыть")}>
          <div className="material-preview-sheet">
            <span>{selectedFile.format || "FILE"}</span>
            <h3>{t(selectedFile.title)}</h3>
            <p>{t("Файл из вашей библиотеки материалов.")}</p>
            <div><strong>{t("Обновлено")}</strong><span>{t(material.updated)}</span></div>
            <div><strong>{t("Категория")}</strong><span>{t(material.category)}</span></div>
          </div>
          <footer className="portal-dialog-actions">
            <button type="button" onClick={openAiHub}><Sparkles size={17} /> {t("Открыть AI Hub")}</button>
            <button type="button" onClick={() => void openMaterialDownload(selectedFile, notify, t)}><Download size={17} /> {t("Скачать")}</button>
          </footer>
        </PortalDialog>
      ) : null}
    </section>
  );
}
