"use client";

import { useEffect, useMemo, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { ChevronLeft, ChevronRight, Plus, Workflow } from "lucide-react";
import type { PartnerStructurePayload, PartnerTreeNode } from "../../../lib/api/partner-types";
import type { NotifyFn, TFn } from "../../../lib/portal";
import { usePortalBackend } from "../../../lib/auth/PortalBackendProvider";
import { PageShell } from "../shared/PageShell";
import { PortalDialog } from "../shared/PortalDialog";
import { PortalLoading } from "../shared/PortalLoading";

const EMPTY_SELF: PartnerTreeNode = {
  id: "self",
  name: "Вы",
  initial: "R",
  rank: "—",
  parentId: null,
  branchId: null,
  level: "L0",
  active: false,
  children: [null, null],
  teamSize: 0,
  activeTeam: 0,
  remainingPv: 0,
};

export function PartnersView({ t, notify, embedded = false }: { t: TFn; notify: NotifyFn; embedded?: boolean }) {
  const router = useRouter();
  const pathname = usePathname();
  const { structure, dashboard, ready } = usePortalBackend();
  const payload = structure as PartnerStructurePayload | null;
  const directory = payload?.tree?.directory ?? {};
  const summary = payload?.summary;
  const legs = payload?.legs;
  const members = payload?.members ?? [];
  const teamDepth = dashboard?.team_depth as { tariff_depth_limit?: number; levels?: Array<{ level: string; total: number; active: number; pv?: number }> } | undefined;
  const depthLimit = Number(teamDepth?.tariff_depth_limit ?? 0);
  const depthLevels = teamDepth?.levels ?? [];
  const [selectedLevel, setSelectedLevel] = useState<string | null>(null);
  const routeParts = pathname.replace(/^\/team\/?/, "").split("/").filter(Boolean);
  const routedFocus = routeParts[0] && routeParts[0] !== "profile" && directory[routeParts[0]]
    ? routeParts[0]
    : "self";
  const routedProfile = routeParts[1] === "profile" && directory[routeParts[2]] ? routeParts[2] : null;
  const [focusedPartnerId, setFocusedPartnerId] = useState(routedFocus);
  const [selectedProfileId, setSelectedProfileId] = useState<string | null>(routedProfile);

  useEffect(() => {
    setFocusedPartnerId(routedFocus);
    setSelectedProfileId(routedProfile);
  }, [routedFocus, routedProfile]);

  const focusedPartner = directory[focusedPartnerId] ?? directory.self ?? EMPTY_SELF;
  const hasTree = Boolean(directory.self);
  const focusRoute = (id: string) => (embedded ? "/cabinet" : id === "self" ? "/team" : `/team/${id}`);
  const openProfile = (id: string) => {
    setSelectedProfileId(id);
    if (!embedded) router.push(`/team/${focusedPartnerId}/profile/${id}`);
  };
  const focusPartner = (id: string) => {
    if (!directory[id] && id !== "self") return;
    if (id === focusedPartnerId) {
      openProfile(id);
      return;
    }
    setFocusedPartnerId(id);
    setSelectedProfileId(null);
    if (!embedded) router.push(focusRoute(id));
  };
  const closeProfile = () => {
    setSelectedProfileId(null);
    if (!embedded) router.replace(focusRoute(focusedPartnerId));
  };
  const formatNumber = (value: number) => new Intl.NumberFormat("ru-RU").format(value);
  const leftLeg = legs?.find((leg) => leg.id === "left");
  const rightLeg = legs?.find((leg) => leg.id === "right");
  const branchIds = ["left", "right"] as const;
  const children = focusedPartner.children ?? [null, null];
  const branches = branchIds.map((id, index) => {
    const partnerId = children[index] ?? null;
    const partner = partnerId ? directory[partnerId] ?? null : null;
    const apiLeg = focusedPartnerId === "self" ? (id === "left" ? leftLeg : rightLeg) : null;
    return {
      id,
      title: id === "left" ? "Левая ветка" : "Правая ветка",
      person: partner,
      remainingPv: Number(apiLeg?.pv ?? partner?.remainingPv ?? 0),
      members: Number(apiLeg?.members ?? partner?.teamSize ?? 0),
      active: Number(apiLeg?.active ?? partner?.activeTeam ?? 0),
    };
  });
  const treeFamilies = branches.map((branch) => ({
    ...branch,
    children: branch.person
      ? (branch.person.children ?? [null, null]).map((childId) => (childId ? directory[childId] ?? null : null))
      : [],
  }));
  const teamLevels = useMemo(
    () => depthLevels.map((row) => [row.level, row.total, row.active] as const),
    [depthLevels],
  );
  const headerTotal = summary?.total_members ?? focusedPartner.teamSize ?? 0;
  const headerActive = summary?.active_members ?? focusedPartner.activeTeam ?? 0;
  const selectedLevelData = teamLevels.find(([level]) => level === selectedLevel);
  const selectedLevelPartners = selectedLevelData
    ? members
        .filter((member) => member.level === selectedLevelData[0])
        .map((member) => ({
          id: member.id,
          name: member.name,
          branch: member.branch,
          active: member.active ?? member.status === "Активен",
        }))
    : [];
  const selectedProfile = selectedProfileId ? directory[selectedProfileId] : null;
  const selectedSponsor = selectedProfile?.parentId ? directory[selectedProfile.parentId] : null;

  if (!embedded && !ready) {
    return (
      <PageShell>
        <PortalLoading label={t("Загрузка команды…")} />
      </PageShell>
    );
  }

  const content = (
    <section className={embedded ? "structure-page structure-page-embedded" : "structure-page"}>
      <div className="team-command-grid">
        <article className="team-command-surface team-tree-surface">
          <header className="team-command-header">
            <div className="team-command-heading">
              <div><strong>{t("Команда")}</strong></div>
              <div className="team-command-heading-metrics">
                <span><strong>{formatNumber(headerTotal)}</strong><small>{t("всего")}</small></span>
                <span><strong>{formatNumber(headerActive)}</strong><small>{t("активных")}</small></span>
              </div>
            </div>
          </header>

          {!hasTree ? (
            <div className="structure-workbench team-workbench">
              <p className="team-tree-empty">{t("Структура появится после оформления тарифа.")}</p>
            </div>
          ) : (
            <section className="structure-workbench team-workbench">
              <div className="structure-network-map team-binary-tree" role="region" aria-label={t("Дерево команды")} key={focusedPartnerId}>
                {focusedPartnerId !== "self" ? (
                  <button type="button" className="team-tree-return" onClick={() => focusPartner("self")}>
                    <ChevronLeft size={15} /><span>{t("Моя структура")}</span>
                  </button>
                ) : null}
                <div className="team-tree-branch-strip">
                  {branches.map((branch) => (
                    <aside className={`team-header-branch is-${branch.id}`} key={branch.id} aria-label={t(branch.title)}>
                      <header><i /><strong>{t(branch.title)}</strong></header>
                      <div>
                        <span><strong>{branch.members}</strong><small>{t("всего")}</small></span>
                        <span><strong>{branch.active}</strong><small>{t("активных")}</small></span>
                        <span><strong>{formatNumber(branch.remainingPv)} PV</strong></span>
                      </div>
                    </aside>
                  ))}
                </div>
                <div className="team-tree-layout">
                  <div className="team-tree-self-row">
                    <button type="button" className="team-tree-person is-self" onClick={() => focusPartner(focusedPartner.id)}>
                      <span>{focusedPartner.initial}</span>
                      <div><strong>{focusedPartner.name}</strong><em>{focusedPartner.rank}</em></div>
                    </button>
                  </div>
                  <div className="team-tree-primary-row">
                    {treeFamilies.map((family) => (
                      <div className={`team-tree-primary-slot is-${family.id}`} key={family.id}>
                        {family.person ? (
                          <button type="button" className={`team-tree-person is-primary is-${family.id}`} onClick={() => focusPartner(family.person!.id)}>
                            <span>{family.person.initial}</span>
                            <div><strong>{family.person.name}</strong><small>{family.person.rank}</small></div>
                          </button>
                        ) : (
                          <button
                            type="button"
                            className={`team-tree-person is-primary is-${family.id} is-empty`}
                            onClick={() => notify(t("Пригласите партнёра — размещение в бинаре произойдёт после покупки тарифа"))}
                          >
                            <span><Plus size={17} /></span>
                            <div><small>{t(family.title)} · L1</small><strong>{t("Свободное место")}</strong><em>{t("Пригласить партнёра")}</em></div>
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                  <div className="team-tree-families">
                    {treeFamilies.map((family) => (
                      <div className={`team-tree-family is-${family.id}`} key={family.id}>
                        {family.person ? (
                          <div className="team-tree-children">
                            {family.children.map((person, index) => (person ? (
                              <button type="button" className={`team-tree-person is-secondary is-${family.id}`} key={person.id} onClick={() => focusPartner(person.id)}>
                                <span>{person.initial}</span>
                                <div><strong>{person.name}</strong><small>{person.rank}</small></div>
                              </button>
                            ) : (
                              <button
                                type="button"
                                className={`team-tree-person is-secondary is-${family.id} is-empty`}
                                key={`${family.person!.id}:${index}`}
                                onClick={() => notify(t("Пригласите партнёра — размещение в бинаре произойдёт после покупки тарифа"))}
                              >
                                <span><Plus size={17} /></span>
                                <div><small>{t(family.title)}</small><strong>{t("Свободное место")}</strong><em>{t("Пригласить партнёра")}</em></div>
                              </button>
                            )))}
                          </div>
                        ) : null}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </section>
          )}
        </article>
        <article className="team-command-surface team-depth-surface">
          <header className="team-depth-header">
            <div className="team-levels-heading"><strong>{t("Глубина")}</strong></div>
          </header>
          <aside className="team-levels team-levels-compact" aria-label={t("Уровни команды")}>
            <div className="team-levels-list">
              {teamLevels.length === 0 ? (
                <p className="team-tree-empty">{t("Пока нет уровней в команде")}</p>
              ) : (
                teamLevels.map(([level, total, active], index) => {
                  const isIncluded = depthLimit <= 0 || index < depthLimit;
                  return (
                    <button type="button" className={`team-level-row${isIncluded ? "" : " is-outside-tier"}`} key={level} onClick={() => setSelectedLevel(level)} aria-label={`${t("Открыть уровень")} ${level}`}>
                      <strong className={isIncluded ? "is-included" : ""}>{level}</strong>
                      <span className="team-level-population"><b>{active}</b><small>{t("активных")} {t("из")} {total}</small></span>
                      <ChevronRight size={16} />
                    </button>
                  );
                })
              )}
            </div>
          </aside>
        </article>
      </div>
      {selectedLevelData ? (
        <PortalDialog title={`${t("Уровень")} ${selectedLevelData[0]}`} eyebrow={t("Партнёры уровня")} onClose={() => setSelectedLevel(null)} className="team-level-dialog" closeLabel={t("Закрыть")}>
          <div className="team-level-dialog-summary">
            <div><span>{t("Всего партнёров")}</span><strong>{selectedLevelData[1]}</strong></div>
            <div><span>{t("Активных партнёров")}</span><strong>{selectedLevelData[2]}</strong></div>
          </div>
          <div className="team-level-dialog-list">
            {selectedLevelPartners.length === 0 ? (
              <p className="team-tree-empty">{t("На этом уровне пока нет партнёров")}</p>
            ) : (
              selectedLevelPartners.map((partner, index) => (
                <button
                  type="button"
                  key={partner.id || `${partner.name}-${index}`}
                  onClick={() => {
                    if (partner.id && directory[partner.id]) {
                      setSelectedLevel(null);
                      openProfile(partner.id);
                    } else {
                      notify(`${partner.name} · ${t("партнёр уровня")}`);
                    }
                  }}
                >
                  <i>{partner.name.slice(0, 1)}</i>
                  <span><strong>{partner.name}</strong><small>{partner.branch}</small></span>
                  <em className={partner.active ? "is-active" : ""}>{partner.active ? t("Активен") : t("Неактивен")}</em>
                  <ChevronRight size={16} />
                </button>
              ))
            )}
          </div>
        </PortalDialog>
      ) : null}
      {selectedProfile ? (
        <PortalDialog title={selectedProfile.name} eyebrow={t("Профиль партнёра")} onClose={closeProfile} className="team-member-profile-dialog" closeLabel={t("Закрыть")}>
          <div className="team-member-profile-hero">
            <i>{selectedProfile.initial}</i>
            <div>
              <strong>{selectedProfile.rank}</strong>
              <span className={selectedProfile.active ? "is-active" : ""}>{selectedProfile.active ? t("Активен") : t("Неактивен")}</span>
            </div>
          </div>
          <div className="team-member-profile-metrics">
            <div><span>{t("Команда")}</span><strong>{formatNumber(selectedProfile.teamSize)}</strong></div>
            <div><span>{t("Активных")}</span><strong>{formatNumber(selectedProfile.activeTeam)}</strong></div>
            <div><span>{t("Уровень")}</span><strong>{selectedProfile.level}</strong></div>
            <div><span>PV</span><strong>{formatNumber(selectedProfile.remainingPv || selectedProfile.pv || 0)}</strong></div>
          </div>
          <div className="team-member-profile-data">
            <div><span>{t("Куратор")}</span><strong>{selectedSponsor ? selectedSponsor.name : "—"}</strong></div>
            <div><span>{t("Ветка")}</span><strong>{selectedProfile.branchId === "right" ? t("Правая ветка") : selectedProfile.branchId === "left" ? t("Левая ветка") : "—"}</strong></div>
          </div>
          <div className="team-member-profile-actions">
            {selectedProfile.id !== focusedPartnerId ? (
              <button type="button" onClick={() => focusPartner(selectedProfile.id)}>
                <Workflow size={16} />{t("Показать структуру")}
              </button>
            ) : null}
          </div>
        </PortalDialog>
      ) : null}
    </section>
  );
  return embedded ? content : <PageShell className="structure-page-shell">{content}</PageShell>;
}
