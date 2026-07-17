"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { ChevronLeft, ChevronRight, Plus, Send, UserPlus, Workflow } from "lucide-react";
import { CURRENT_DEMO_TIER } from "../../../lib/marketing-plan";
import { TEAM_PARTNER_DIRECTORY } from "../../../lib/portal";
import type { NotifyFn, TFn } from "../../../lib/portal";
import { usePortalBackend } from "../../../lib/auth/PortalBackendProvider";
import { PageShell } from "../shared/PageShell";
import { PortalDialog } from "../shared/PortalDialog";
import { PortalLoading } from "../shared/PortalLoading";

export function PartnersView({ t, notify, embedded = false }: { t: TFn; notify: NotifyFn; embedded?: boolean }) {
  const router = useRouter();
  const pathname = usePathname();
  const { structure, dashboard, ready } = usePortalBackend();
  const summary = (structure as { summary?: { total_members?: number; active_members?: number; total_pv?: number } } | null)?.summary;
  const legs = (structure as { legs?: Array<{ id: string; title?: string; members?: number; active?: number; pv?: number }> } | null)?.legs;
  const depthLevels = (dashboard?.team_depth as { levels?: Array<{ level: string; total: number; active: number; pv?: number }> } | undefined)?.levels;
  const [selectedLevel, setSelectedLevel] = useState<string | null>(null);
  const routeParts = pathname.replace(/^\/team\/?/, "").split("/").filter(Boolean);
  const routedFocus = routeParts[0] && routeParts[0] !== "profile" && TEAM_PARTNER_DIRECTORY[routeParts[0]] ? routeParts[0] : "self";
  const routedProfile = routeParts[1] === "profile" && TEAM_PARTNER_DIRECTORY[routeParts[2]] ? routeParts[2] : null;
  const [focusedPartnerId, setFocusedPartnerId] = useState(routedFocus);
  const [selectedProfileId, setSelectedProfileId] = useState<string | null>(routedProfile);
  const [placementSlot, setPlacementSlot] = useState<{ key: string; branch: string; level: string } | null>(null);
  const [slotAssignments, setSlotAssignments] = useState<Record<string, string>>({});

  useEffect(() => {
    setFocusedPartnerId(routedFocus);
    setSelectedProfileId(routedProfile);
  }, [routedFocus, routedProfile]);

  const focusedPartner = TEAM_PARTNER_DIRECTORY[focusedPartnerId] ?? TEAM_PARTNER_DIRECTORY.self;
  const focusRoute = (id: string) => embedded ? "/cabinet" : id === "self" ? "/team" : `/team/${id}`;
  const openProfile = (id: string) => {
    setSelectedProfileId(id);
    if (!embedded) router.push(`/team/${focusedPartnerId}/profile/${id}`);
  };
  const focusPartner = (id: string) => {
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
  const resolveSlot = (parentId: string, position: number, partnerId: string | null) => (
    partnerId ?? slotAssignments[`${parentId}:${position}`] ?? null
  );
  const formatNumber = (value: number) => new Intl.NumberFormat("ru-RU").format(value);
  const leftLeg = legs?.find((leg) => leg.id === "left");
  const rightLeg = legs?.find((leg) => leg.id === "right");
  const branchIds = ["left", "right"] as const;
  const branches = branchIds.map((id, index) => {
    const partnerId = resolveSlot(focusedPartner.id, index, focusedPartner.children[index]);
    const partner = partnerId ? TEAM_PARTNER_DIRECTORY[partnerId] : null;
    const apiLeg = id === "left" ? leftLeg : rightLeg;
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
      ? branch.person.children.map((childId, index) => {
          const resolvedId = resolveSlot(branch.person!.id, index, childId);
          return resolvedId ? TEAM_PARTNER_DIRECTORY[resolvedId] : null;
        })
      : [],
  }));
  const partners = Object.values(TEAM_PARTNER_DIRECTORY).filter((partner) => partner.id !== "andrey" && partner.id !== "self");
  const teamLevels = (depthLevels?.length
    ? depthLevels.map((row) => [row.level, row.total, row.active] as const)
    : [
    ["L1", 35, 15], ["L2", 48, 18], ["L3", 41, 11],
    ["L4", 29, 7], ["L5", 23, 2], ["L6", 18, 2],
    ["L7", 14, 1], ["L8", 9, 1], ["L9", 6, 1],
    ["L10", 4, 0], ["L11", 3, 0], ["L12", 2, 0], ["L13", 2, 0],
  ]) as ReadonlyArray<readonly [string, number, number]>;
  const headerTotal = summary?.total_members ?? focusedPartner.teamSize;
  const headerActive = summary?.active_members ?? focusedPartner.activeTeam;
  const selectedLevelData = teamLevels.find(([level]) => level === selectedLevel);
  const levelPartnerNames = ["Мария К.", "Олег Н.", "Анна С.", "Дмитрий В.", "Елена Р.", "Сергей Б.", "Павел Д.", "Алина Т.", "Виктор Л.", "Екатерина С.", "Антон Р.", "Ольга М."];
  const selectedLevelPartners = selectedLevelData
    ? Array.from({ length: selectedLevelData[1] }, (_, index) => {
        const knownPartner = partners.find((partner) => partner.level === selectedLevelData[0] && partners.filter((item) => item.level === selectedLevelData[0]).indexOf(partner) === index);
        const name = knownPartner?.name ?? `${levelPartnerNames[index % levelPartnerNames.length]} ${index >= levelPartnerNames.length ? index + 1 : ""}`.trim();
        return {
          name,
          branch: knownPartner ? (knownPartner.branchId === "right" ? "Правая ветка" : "Левая ветка") : (index % 2 === 0 ? "Левая ветка" : "Правая ветка"),
          active: index < selectedLevelData[2],
        };
      })
    : [];

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

        <section className="structure-workbench team-workbench">
            <div className="structure-network-map team-binary-tree" role="region" aria-label={t("Дерево команды")} key={focusedPartnerId}>
              {focusedPartnerId !== "self" ? (
                <button type="button" className="team-tree-return" onClick={() => focusPartner("self")}><ChevronLeft size={15} /><span>{t("Моя структура")}</span></button>
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
                    <div><strong>{t(focusedPartner.name)}</strong><em>{t(focusedPartner.rank)}</em></div>
                  </button>
                </div>
                <div className="team-tree-primary-row">
                  {treeFamilies.map((family) => (
                    <div className={`team-tree-primary-slot is-${family.id}`} key={family.id}>
                      {family.person ? (
                        <button type="button" className={`team-tree-person is-primary is-${family.id}`} onClick={() => focusPartner(family.person!.id)}>
                          <span>{family.person.initial}</span>
                          <div><strong>{t(family.person.name)}</strong><small>{t(family.person.rank)}</small></div>
                        </button>
                      ) : (
                        <button type="button" className={`team-tree-person is-primary is-${family.id} is-empty`} onClick={() => setPlacementSlot({ key: `${focusedPartner.id}:${family.id === "left" ? 0 : 1}`, branch: family.title, level: "L1" })}>
                          <span><Plus size={17} /></span><div><small>{t(family.title)} · L1</small><strong>{t("Свободное место")}</strong><em>{t("Разместить партнёра")}</em></div>
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
                          {family.children.map((person, index) => person ? (
                            <button type="button" className={`team-tree-person is-secondary is-${family.id}`} key={person.id} onClick={() => focusPartner(person.id)}>
                              <span>{person.initial}</span>
                              <div><strong>{t(person.name)}</strong><small>{t(person.rank)}</small></div>
                            </button>
                          ) : (
                            <button type="button" className={`team-tree-person is-secondary is-${family.id} is-empty`} key={`${family.person!.id}:${index}`} onClick={() => setPlacementSlot({ key: `${family.person!.id}:${index}`, branch: family.title, level: `L${Number.parseInt(family.person!.level.slice(1) || "1", 10) + 1}` })}>
                              <span><Plus size={17} /></span><div><small>{t(family.title)}</small><strong>{t("Свободное место")}</strong><em>{t("Разместить партнёра")}</em></div>
                            </button>
                          ))}
                        </div>
                      ) : null}
                    </div>
                  ))}
                </div>
              </div>
            </div>
        </section>
        </article>
        <article className="team-command-surface team-depth-surface">
            <header className="team-depth-header">
              <div className="team-levels-heading"><strong>{t("Глубина")}</strong></div>
            </header>
            <aside className="team-levels team-levels-compact" aria-label={t("Уровни команды")}>
              <div className="team-levels-list">
                {teamLevels.map(([level, total, active], index) => {
                  const isIncluded = index < CURRENT_DEMO_TIER.binaryDepth;
                  return (
                    <button type="button" className={`team-level-row${isIncluded ? "" : " is-outside-tier"}`} key={level} onClick={() => setSelectedLevel(level)} aria-label={`${t("Открыть уровень")} ${level}`}>
                      <strong className={isIncluded ? "is-included" : ""}>{level}</strong>
                      <span className="team-level-population"><b>{active}</b><small>{t("активных")} {t("из")} {total}</small></span>
                      <ChevronRight size={16} />
                    </button>
                  );
                })}
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
              {selectedLevelPartners.map((partner, index) => (
                <button type="button" key={`${partner.name}-${index}`} onClick={() => notify(`${t(partner.name)} · ${t("карточка партнёра")}`)}>
                  <i>{partner.name.slice(0, 1)}</i>
                  <span><strong>{t(partner.name)}</strong><small>{t(partner.branch)}</small></span>
                  <em className={partner.active ? "is-active" : ""}>{partner.active ? t("Активен") : t("Неактивен")}</em>
                  <ChevronRight size={16} />
                </button>
              ))}
            </div>
          </PortalDialog>
        ) : null}
        {selectedProfileId ? (() => {
          const profile = TEAM_PARTNER_DIRECTORY[selectedProfileId];
          const sponsor = profile.sponsorId ? TEAM_PARTNER_DIRECTORY[profile.sponsorId] : null;
          return (
            <PortalDialog title={t(profile.name)} eyebrow={t("Профиль партнёра")} onClose={closeProfile} className="team-member-profile-dialog" closeLabel={t("Закрыть")}>
              <div className="team-member-profile-hero">
                <i>{profile.initial}</i>
                <div><strong>{t(profile.rank)}</strong><span className={profile.active ? "is-active" : ""}>{t(profile.active ? "Активен" : "Неактивен")}</span></div>
              </div>
              <div className="team-member-profile-metrics">
                <div><span>{t("Команда")}</span><strong>{formatNumber(profile.teamSize)}</strong></div>
                <div><span>{t("Активных")}</span><strong>{formatNumber(profile.activeTeam)}</strong></div>
                <div><span>{t("Уровень")}</span><strong>{profile.level}</strong></div>
              </div>
              <div className="team-member-profile-data">
                <div><span>{t("Куратор")}</span><strong>{sponsor ? t(sponsor.name) : "—"}</strong></div>
                <div><span>Telegram</span><strong>{profile.telegram}</strong></div>
                <div><span>{t("Телефон")}</span><strong>{profile.phone}</strong></div>
              </div>
              <div className="team-member-profile-actions">
                <button type="button" onClick={() => notify(`${t("Сообщение для")} ${t(profile.name)}`)}><Send size={16} />{t("Написать")}</button>
                {profile.id !== focusedPartnerId ? <button type="button" onClick={() => focusPartner(profile.id)}><Workflow size={16} />{t("Показать структуру")}</button> : null}
              </div>
            </PortalDialog>
          );
        })() : null}
        {placementSlot ? (
          <PortalDialog title={t("Свободное место")} eyebrow={`${t(placementSlot.branch)} · ${placementSlot.level}`} onClose={() => setPlacementSlot(null)} className="team-placement-dialog" closeLabel={t("Закрыть")}>
            <p>{t("Выберите лично приглашённого партнёра для размещения в этой позиции.")}</p>
            <button type="button" className="team-placement-candidate" onClick={() => {
              setSlotAssignments((current) => ({ ...current, [placementSlot.key]: "anna" }));
              setPlacementSlot(null);
              notify(t("Анна С. размещена в структуре"));
            }}><i>А</i><span><strong>{t("Анна С.")}</strong><small>{t("Готова к размещению")}</small></span><ChevronRight size={16} /></button>
            <button type="button" className="team-placement-invite" onClick={() => notify(t("Открыто приглашение нового партнёра"))}><UserPlus size={16} />{t("Пригласить нового партнёра")}</button>
          </PortalDialog>
        ) : null}
      </section>
  );
  return embedded ? content : <PageShell className="structure-page-shell">{content}</PageShell>;
}
