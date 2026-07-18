"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { fetchPrograms } from "../api/academy";
import { fetchChats, fetchMaterials } from "../api/content";
import { fetchCrmKanban } from "../api/crm";
import { fetchHome, type HomePayload } from "../api/home";
import { fetchIboxScenarios } from "../api/ibox";
import { fetchNotifications } from "../api/me";
import { fetchInvited, fetchPartnerDashboard, fetchPartnerStructure } from "../api/partner";
import { fetchTariffs, fetchTokenPacks } from "../api/store";
import { fetchWallet } from "../api/wallet";
import { useAuth } from "../auth/AuthProvider";

type PortalBackendValue = {
  ready: boolean;
  home: HomePayload | null;
  tariffs: Array<Record<string, unknown>>;
  tokens: Array<Record<string, unknown>>;
  dashboard: Record<string, unknown> | null;
  structure: Record<string, unknown> | null;
  invited: unknown;
  wallet: Record<string, unknown> | null;
  programs: unknown;
  materials: unknown;
  chats: unknown;
  crm: unknown;
  ibox: unknown;
  notifications: Array<Record<string, unknown>>;
  reload: () => Promise<void>;
};

const PortalBackendContext = createContext<PortalBackendValue | null>(null);

export function PortalBackendProvider({ children }: { children: ReactNode }) {
  const { user, loading: authLoading } = useAuth();
  const userId = user?.id ?? null;
  const [ready, setReady] = useState(false);
  const [home, setHome] = useState<HomePayload | null>(null);
  const [tariffs, setTariffs] = useState<Array<Record<string, unknown>>>([]);
  const [tokens, setTokens] = useState<Array<Record<string, unknown>>>([]);
  const [dashboard, setDashboard] = useState<Record<string, unknown> | null>(null);
  const [structure, setStructure] = useState<Record<string, unknown> | null>(null);
  const [invited, setInvited] = useState<unknown>(null);
  const [wallet, setWallet] = useState<Record<string, unknown> | null>(null);
  const [programs, setPrograms] = useState<unknown>(null);
  const [materials, setMaterials] = useState<unknown>(null);
  const [chats, setChats] = useState<unknown>(null);
  const [crm, setCrm] = useState<unknown>(null);
  const [ibox, setIbox] = useState<unknown>(null);
  const [notifications, setNotifications] = useState<Array<Record<string, unknown>>>([]);
  const requestIdRef = useRef(0);

  const reload = useCallback(async () => {
    if (!userId) {
      setReady(false);
      return;
    }
    const requestId = ++requestIdRef.current;
    try {
      const [
        homeData,
        tariffData,
        tokenData,
        dashData,
        invitedData,
        walletData,
        programsData,
        materialsData,
        chatsData,
        crmData,
        iboxData,
        notifData,
      ] = await Promise.all([
        fetchHome().catch(() => null),
        fetchTariffs().catch(() => []),
        fetchTokenPacks().catch(() => []),
        fetchPartnerDashboard().catch(() => null),
        fetchInvited().catch(() => null),
        fetchWallet().catch(() => null),
        fetchPrograms().catch(() => null),
        fetchMaterials().catch(() => null),
        fetchChats().catch(() => null),
        fetchCrmKanban().catch(() => null),
        fetchIboxScenarios().catch(() => null),
        fetchNotifications().catch(() => []),
      ]);
      if (requestId !== requestIdRef.current) return;

      const depthLimit = Number(
        (dashData as { team_depth?: { tariff_depth_limit?: number } } | null)?.team_depth?.tariff_depth_limit ?? 0,
      );
      const structureDepth = Math.min(Math.max(depthLimit || 15, 1), 15);
      const structureData = await fetchPartnerStructure({ depth: structureDepth }).catch(() => null);
      if (requestId !== requestIdRef.current) return;

      setHome(homeData);
      setTariffs(tariffData as Array<Record<string, unknown>>);
      setTokens(tokenData as Array<Record<string, unknown>>);
      setDashboard(dashData as Record<string, unknown> | null);
      setStructure(structureData as Record<string, unknown> | null);
      setInvited(invitedData);
      setWallet(walletData as Record<string, unknown> | null);
      setPrograms(programsData);
      setMaterials(materialsData);
      setChats(chatsData);
      setCrm(crmData);
      setIbox(iboxData);
      setNotifications(Array.isArray(notifData) ? (notifData as Array<Record<string, unknown>>) : []);
    } finally {
      if (requestId === requestIdRef.current) setReady(true);
    }
  }, [userId]);

  useEffect(() => {
    if (authLoading) return;
    if (!userId) {
      setReady(false);
      return;
    }
    void reload();
  }, [authLoading, userId, reload]);

  const value = useMemo(
    () => ({
      ready,
      home,
      tariffs,
      tokens,
      dashboard,
      structure,
      invited,
      wallet,
      programs,
      materials,
      chats,
      crm,
      ibox,
      notifications,
      reload,
    }),
    [
      ready,
      home,
      tariffs,
      tokens,
      dashboard,
      structure,
      invited,
      wallet,
      programs,
      materials,
      chats,
      crm,
      ibox,
      notifications,
      reload,
    ],
  );

  return (
    <PortalBackendContext.Provider value={value}>{children}</PortalBackendContext.Provider>
  );
}

export function usePortalBackend() {
  const ctx = useContext(PortalBackendContext);
  if (!ctx) throw new Error("usePortalBackend must be used within PortalBackendProvider");
  return ctx;
}
