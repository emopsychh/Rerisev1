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

function guessExtension(file: MaterialFileRow): string {
  const format = (file.format || "").toLowerCase();
  if (format.includes("pdf")) return ".pdf";
  if (format.includes("doc")) return ".docx";
  if (format.includes("xls")) return ".xlsx";
  if (format.includes("ppt")) return ".pptx";
  if (format.includes("zip")) return ".zip";
  if (format.includes("png")) return ".png";
  if (format.includes("jpg") || format.includes("jpeg")) return ".jpg";
  const fromUrl = file.file_url?.match(/\.([a-z0-9]+)(?:\?|$)/i);
  if (fromUrl) return `.${fromUrl[1].toLowerCase()}`;
  return "";
}

function downloadFileName(file: MaterialFileRow): string {
  const base = (file.title || `file-${file.id}`).replace(/[\\/:*?"<>|]+/g, "_").trim();
  const ext = guessExtension(file);
  if (!ext) return base;
  return base.toLowerCase().endsWith(ext) ? base : `${base}${ext}`;
}

async function openMaterialDownload(file: MaterialFileRow, notify: NotifyFn, t: TFn): Promise<boolean> {
  if (file.file_url && /^https?:\/\//i.test(file.file_url)) {
    window.open(file.file_url, "_blank", "noopener,noreferrer");
    return true;
  }
  try {
    const token = getAccessToken();
    const response = await fetch(`${getApiBaseUrl()}/materials/files/${file.id}/download`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      redirect: "follow",
    });
    if (!response.ok) {
      notify(t("Не удалось скачать файл"));
      return false;
    }
    const blob = await response.blob();
    const objectUrl = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = objectUrl;
    link.download = downloadFileName(file);
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(objectUrl);
    return true;
  } catch {
    notify(t("Не удалось скачать файл"));
    return false;
  }
}

async function downloadAllMaterials(files: MaterialFileRow[], notify: NotifyFn, t: TFn) {
  if (!files.length) return;
  if (files.length === 1) {
    await openMaterialDownload(files[0], notify, t);
    return;
  }

  let ok = 0;
  for (let index = 0; index < files.length; index += 1) {
    const success = await openMaterialDownload(files[index], notify, t);
    if (success) ok += 1;
    // Пауза, чтобы браузер не блокировал пачку загрузок.
    if (index < files.length - 1) {
      await new Promise((resolve) => window.setTimeout(resolve, 450));
    }
  }
  if (ok === files.length) {
    notify(t(`Скачано файлов: ${ok}`));
  } else if (ok > 0) {
    notify(t(`Скачано ${ok} из ${files.length}. Остальные откройте в списке.`));
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
  const [downloadingAll, setDownloadingAll] = useState(false);
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

  const handleDownloadAll = async () => {
    if (!files.length || downloadingAll) return;
    setDownloadingAll(true);
    try {
      await downloadAllMaterials(files, notify, t);
    } finally {
      setDownloadingAll(false);
    }
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
            disabled={!files.length || downloadingAll}
            onClick={() => void handleDownloadAll()}
          >
            <Download size={16} />
            {downloadingAll
              ? t("Скачиваем…")
              : files.length > 1
                ? t("Скачать все")
                : t("Скачать")}
          </button>
        </div>
        {loading ? <PortalLoading label={t("Загрузка файлов…")} /> : null}
        {loadError ? <div className="materials-empty"><strong>{loadError}</strong></div> : null}
        {!loading && !loadError && files.length === 0 ? (
          <div className="materials-empty"><strong>{t("Файлы пока не добавлены")}</strong></div>
        ) : null}
        <div className="material-file-list">
          {files.map((file) => (
            <div className="material-file-row" key={file.id}>
              <button type="button" className="material-file-open" onClick={() => openFile(file.id)}>
                <span>{file.format || "FILE"}</span>
                <div>
                  <strong>{t(file.title)}</strong>
                  <small>{t("обновлено")}: {t(material.updated)}</small>
                </div>
                <ChevronRight size={20} />
              </button>
              <button
                type="button"
                className="material-file-download"
                aria-label={t("Скачать")}
                title={t("Скачать")}
                onClick={(event) => {
                  event.stopPropagation();
                  void openMaterialDownload(file, notify, t);
                }}
              >
                <Download size={16} />
              </button>
            </div>
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
