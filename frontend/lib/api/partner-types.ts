export type PartnerTreeNode = {
  id: string;
  name: string;
  initial: string;
  rank: string;
  parentId: string | null;
  branchId: string | null;
  level: string;
  active: boolean;
  children: [string | null, string | null] | Array<string | null>;
  teamSize: number;
  activeTeam: number;
  remainingPv: number;
  pv?: number;
};

export type PartnerStructureMember = {
  id?: string;
  name: string;
  branch: string;
  branch_id: string;
  level: string;
  pv: number;
  status: string;
  activity: string;
  active?: boolean;
};

export type PartnerStructurePayload = {
  legs?: Array<{
    id: string;
    title?: string;
    members?: number;
    active?: number;
    pv?: number;
    lead?: string | null;
  }>;
  summary?: {
    total_members?: number;
    active_members?: number;
    personal_invites?: number;
    total_pv?: number;
  };
  members?: PartnerStructureMember[];
  tree?: {
    root_id?: string;
    directory?: Record<string, PartnerTreeNode>;
  };
};

export type PartnerTeamDepth = {
  tariff_depth_limit?: number;
  levels?: Array<{ level: string; total: number; active: number; pv?: number }>;
};
