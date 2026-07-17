"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { ChevronRight, Download, Sparkles } from "lucide-react";
import { materialCards, routeSlug } from "../../../lib/portal";
import type { NotifyFn, TFn } from "../../../lib/portal";
import { PortalDialog } from "../shared/PortalDialog";

export function MaterialDetailView({ material, t, notify, openAiBox }: { material: (typeof materialCards)[number]; t: TFn; notify: NotifyFn; openAiBox: () => void }) {
  const router = useRouter();
  const pathname = usePathname();
  const Icon = material.icon;
  const files: Array<[string, string]> = [
    ["Стартовый набор", "PDF"],
    ["Шаблон для встречи", "DOC"],
    ["Готовый сценарий", "PROMPT"],
    ["Короткая версия для чата", "TXT"],
    ["Пример заполнения", "RE:RISE"],
    ["Архив дополнительных материалов", "ZIP"],
  ];
  const materialPath = `/materials/${routeSlug(material.title)}`;
  const fileFromPath = pathname.match(/^\/materials\/[^/]+\/files\/(\d+)$/);
  const [selectedFileIndex, setSelectedFileIndex] = useState<number | null>(() => {
    const fileNumber = fileFromPath ? Number(fileFromPath[1]) : 0;
    return fileNumber >= 1 && fileNumber <= files.length ? fileNumber - 1 : null;
  });
  const selectedFile = selectedFileIndex !== null ? files[selectedFileIndex] : null;
  const openFile = (fileIndex: number) => {
    setSelectedFileIndex(fileIndex);
    router.push(`${materialPath}/files/${fileIndex + 1}`, { scroll: false });
  };
  const closeFile = () => {
    setSelectedFileIndex(null);
    router.push(materialPath, { scroll: false });
  };

  useEffect(() => {
    const fileMatch = pathname.match(/^\/materials\/[^/]+\/files\/(\d+)$/);
    const fileNumber = fileMatch ? Number(fileMatch[1]) : 0;
    setSelectedFileIndex(fileNumber >= 1 && fileNumber <= files.length ? fileNumber - 1 : null);
  }, [pathname, files.length]);

  return (
    <section className="detail-layout">
      <article className={`detail-hero ${material.color}`}>
        <div>
          <span>{material.count} {t("файлов")}</span>
          <h2>{t(material.title)}</h2>
          <p>{t(material.text)}</p>
        </div>
        <div className="detail-hero-icon" aria-hidden="true">
          <Icon size={42} />
        </div>
      </article>

      <section className="detail-list-card">
        <div className="rail-title">
          <h3>{t("Файлы и шаблоны")}</h3>
          <button onClick={() => notify(`${material.title}: подборка подготовлена к скачиванию`)}><Download size={16} /> {t("Скачать все")}</button>
        </div>
        <div className="material-file-list">
          {files.map(([title, kind], index) => (
            <button key={title} onClick={() => openFile(index)}>
              <span>{kind}</span>
              <div>
                <strong>{t(title)}</strong>
                <small>{t("обновлено")}: {t(material.updated)}</small>
              </div>
              <ChevronRight size={20} />
            </button>
          ))}
        </div>
      </section>

      <aside className="detail-side-card">
        <span>{t("Раздел")}</span>
        <strong>{material.count}</strong>
        <p>{t("Материал доступен в вашем текущем аккаунте. Тарифные права будут уточнены отдельно.")}</p>
        <button onClick={openAiBox}>{t("Открыть в AI Hub")}</button>
      </aside>

      {selectedFile ? (
        <PortalDialog title={t(selectedFile[0])} eyebrow={`${t(material.title)} · ${selectedFile[1]}`} onClose={closeFile} className="material-preview-dialog" closeLabel={t("Закрыть")}>
          <div className="material-preview-sheet">
            <span>{selectedFile[1]}</span>
            <h3>{t(selectedFile[0])}</h3>
            <p>{t("Готовая структура с пояснениями, примерами формулировок и рекомендациями по применению.")}</p>
            <div><strong>{t("Обновлено")}</strong><span>{t(material.updated)}</span></div>
            <div><strong>{t("Категория")}</strong><span>{t(material.category)}</span></div>
            <div><strong>{t("Доступ")}</strong><span>{t("Открыт")}</span></div>
          </div>
          <footer className="portal-dialog-actions">
            <button onClick={() => notify(`${t(selectedFile[0])}: ${t("добавлен в AI Hub")}`)}><Sparkles size={17} /> {t("Добавить в AI Hub")}</button>
            <button onClick={() => notify(`${t(selectedFile[0])}: ${t("подготовлен к скачиванию")}`)}><Download size={17} /> {t("Скачать")}</button>
          </footer>
        </PortalDialog>
      ) : null}
    </section>
  );
}
