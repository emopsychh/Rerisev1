export type PartnerTierId = "rise" | "rise-pro" | "rise-pro-max";

export type PartnerTier = {
  id: PartnerTierId;
  name: "Rise" | "Rise Pro" | "Rise Pro Max";
  priceUsd: number;
  includedMonths: number;
  personalBonusCapUsd: number;
  purchasePvCap: number;
  binaryDepth: number;
  matchingLines: number;
  quickStartEligible: boolean;
};

export type PartnerRank = {
  name: string;
  weeklyCollapsedPv: number;
  requirement: string;
  rewardUsd: number;
};

export type PartnerActivityState = "active" | "inactive_with_retained_plan" | "inactive_without_plan";

export type PurchaseReward = {
  cashUsd: number;
  pv: number;
};

/**
 * Canonical owner-approved values used by the portal UI.
 * Open product, payment and withdrawal decisions deliberately do not live here.
 */
export const PARTNER_TIERS = [
  { id: "rise", name: "Rise", priceUsd: 90, includedMonths: 1, personalBonusCapUsd: 30, purchasePvCap: 30, binaryDepth: 3, matchingLines: 1, quickStartEligible: false },
  { id: "rise-pro", name: "Rise Pro", priceUsd: 300, includedMonths: 1, personalBonusCapUsd: 90, purchasePvCap: 90, binaryDepth: 9, matchingLines: 2, quickStartEligible: true },
  { id: "rise-pro-max", name: "Rise Pro Max", priceUsd: 900, includedMonths: 1, personalBonusCapUsd: 300, purchasePvCap: 300, binaryDepth: 15, matchingLines: 3, quickStartEligible: true },
] as const satisfies readonly PartnerTier[];

export const PERSONAL_REWARD_MATRIX = {
  rise: {
    rise: { cashUsd: 30, pv: 30 },
    "rise-pro": { cashUsd: 30, pv: 30 },
    "rise-pro-max": { cashUsd: 30, pv: 30 },
  },
  "rise-pro": {
    rise: { cashUsd: 30, pv: 30 },
    "rise-pro": { cashUsd: 90, pv: 90 },
    "rise-pro-max": { cashUsd: 90, pv: 90 },
  },
  "rise-pro-max": {
    rise: { cashUsd: 30, pv: 30 },
    "rise-pro": { cashUsd: 90, pv: 90 },
    "rise-pro-max": { cashUsd: 300, pv: 300 },
  },
} as const satisfies Record<PartnerTierId, Record<PartnerTierId, PurchaseReward>>;

/**
 * Approved differential rewards only. Upgrade price and subscription-period effects
 * are intentionally omitted because the owner has not approved them.
 */
export const UPGRADE_REWARD_MATRIX = {
  "rise-to-rise-pro": {
    rise: { cashUsd: 0, pv: 0 },
    "rise-pro": { cashUsd: 60, pv: 60 },
    "rise-pro-max": { cashUsd: 60, pv: 60 },
  },
  "rise-pro-to-rise-pro-max": {
    rise: { cashUsd: 0, pv: 0 },
    "rise-pro": { cashUsd: 0, pv: 0 },
    "rise-pro-max": { cashUsd: 210, pv: 210 },
  },
  "rise-to-rise-pro-max": {
    rise: { cashUsd: 0, pv: 0 },
    "rise-pro": { cashUsd: 60, pv: 60 },
    "rise-pro-max": { cashUsd: 270, pv: 270 },
  },
} as const satisfies Record<string, Record<PartnerTierId, PurchaseReward>>;

export const PARTNER_RANKS = [
  { name: "Партнёр I", weeklyCollapsedPv: 0, requirement: "Покупка любого партнёрского тарифа", rewardUsd: 0 },
  { name: "Партнёр II", weeklyCollapsedPv: 100, requirement: "2 активных личных партнёра", rewardUsd: 10 },
  { name: "Партнёр III", weeklyCollapsedPv: 200, requirement: "4 активных личных партнёра", rewardUsd: 20 },
  { name: "Эксперт I", weeklyCollapsedPv: 300, requirement: "6 активных личных партнёров", rewardUsd: 30 },
  { name: "Эксперт II", weeklyCollapsedPv: 400, requirement: "8 активных личных партнёров", rewardUsd: 40 },
  { name: "Эксперт III", weeklyCollapsedPv: 500, requirement: "10 активных личных партнёров", rewardUsd: 50 },
  { name: "Мастер I", weeklyCollapsedPv: 600, requirement: "Эксперт I или выше в каждой бинарной ноге", rewardUsd: 60 },
  { name: "Мастер II", weeklyCollapsedPv: 700, requirement: "Эксперт II или выше в каждой бинарной ноге", rewardUsd: 70 },
  { name: "Гранд-мастер", weeklyCollapsedPv: 800, requirement: "Эксперт III или выше в каждой бинарной ноге", rewardUsd: 80 },
  { name: "Лидер I", weeklyCollapsedPv: 1000, requirement: "Мастер I или выше в каждой бинарной ноге", rewardUsd: 100 },
  { name: "Лидер II", weeklyCollapsedPv: 1500, requirement: "Мастер II или выше в каждой бинарной ноге", rewardUsd: 150 },
  { name: "Топ-лидер", weeklyCollapsedPv: 2000, requirement: "Гранд-мастер или выше в каждой бинарной ноге", rewardUsd: 200 },
  { name: "Ментор I", weeklyCollapsedPv: 3000, requirement: "Лидер I или выше в каждой бинарной ноге", rewardUsd: 300 },
  { name: "Ментор II", weeklyCollapsedPv: 4000, requirement: "Лидер II или выше в каждой бинарной ноге", rewardUsd: 400 },
  { name: "Премьер-ментор", weeklyCollapsedPv: 5000, requirement: "Топ-лидер или выше в каждой бинарной ноге", rewardUsd: 500 },
  { name: "Визионер", weeklyCollapsedPv: 10000, requirement: "Ментор I или выше в каждой бинарной ноге", rewardUsd: 10000 },
] as const satisfies readonly PartnerRank[];

export const SUBSCRIPTION_RULES = {
  monthlyPriceUsd: 30,
  periodLabel: "месяц",
  /** Calendar month versus a rolling number of days is not yet approved. */
  periodCalculation: null,
  directSponsorRewardUsd: 9,
  generatedPv: 9,
  firstIncludedMonthIsRenewal: false,
  undistributedSponsorRewardRule: null,
  /** Owner decision dated 2026-07-15: there is no global nine-level cap. */
  pvDepthByTier: { rise: 3, "rise-pro": 9, "rise-pro-max": 15 } satisfies Record<PartnerTierId, number>,
} as const;

export const BINARY_RULES = {
  collapsedPvPerUsd: 10,
  legs: 2,
  unusedPvCarriesForward: true,
  incomeCap: null,
  calculationMode: "real_time",
  inactiveBalanceMode: "frozen",
  resetAfterContinuousInactivityMonths: 12,
  /** Whether only complete blocks of 10 PV pay out has not been approved. */
  rounding: null,
} as const;

export const MATCHING_RULES = {
  percentOfBinaryIncome: 10,
  sponsorLinesByTier: { rise: 1, "rise-pro": 2, "rise-pro-max": 3 } satisfies Record<PartnerTierId, number>,
  inactiveCompression: false,
  incomeCap: null,
} as const;

export const QUICK_START_RULES = {
  eligibleTierIds: ["rise-pro", "rise-pro-max"] as const,
  windowDays: 30,
  requiredPersonalPartners: 4,
  qualifyingPurchaseTierIds: ["rise-pro", "rise-pro-max"] as const,
  rewardUsd: 90,
  rewardOnce: true,
  upgradeRestartsWindow: false,
  retroactiveEligibilityAfterOwnUpgrade: false,
  invitedPartnerUpgradeCounts: null,
} as const;

export const QUALIFICATION_PERIOD = {
  timezone: "Europe/Moscow",
  starts: "Понедельник, 00:00",
  ends: "Воскресенье, 23:59:59",
} as const;

export const RANK_RULES = {
  permanentOnceAwarded: true,
  activePartnerRequired: true,
  recurringConfirmationRequired: false,
  onlyHighestNewRewardInWeek: true,
  skippedRewardsAreNotCompensated: true,
  /** Real-time award conflicts with the highest-only weekly rule and stays unresolved. */
  payoutTiming: null,
} as const;

/** Structured qualifiers shared by the future rank engine and explanatory UI. */
export const RANK_QUALIFICATION_RULES = {
  personalPartnerRanks: {
    fromRank: "Партнёр II",
    throughRank: "Эксперт III",
    directInvitesOnly: true,
    activeAtQualification: true,
    eligibleTierIds: ["rise", "rise-pro", "rise-pro-max"] as const,
  },
  binaryLegQualifierRanks: {
    fromRank: "Мастер I",
    distinctPartners: 2,
    onePerBinaryLeg: true,
    anyPhysicalDepth: true,
    activeAtQualification: true,
    mustAlreadyHoldRequiredRank: true,
    laterInactivityDoesNotRevokeAwardedRank: true,
  },
} as const;

export const ACTIVITY_RULES = {
  includedFirstMonth: true,
  renewalPriceUsd: 30,
  renewalPeriodCalculation: null,
  retainedPlanMonths: 12,
  states: {
    active: "Первый включённый месяц или оплаченное продление",
    inactive_with_retained_plan: "Тариф и структура сохранены, старый PV заморожен, командные начисления недоступны",
    inactive_without_plan: "После 12 месяцев тариф и PV обнулены, аккаунт, структура и исторический статус сохранены",
  } satisfies Record<PartnerActivityState, string>,
} as const;

export const PLACEMENT_RULES = {
  sponsorIsImmutable: true,
  binaryPositionIsImmutable: true,
  firstPersonalPartnerUsesSponsorsOuterLeg: true,
  laterPersonalPartnersAllowLegChoice: true,
  exactFreePositionAlgorithm: null,
  spilloverKeepsActualInviterAsSponsor: true,
} as const;

export const CORRECTION_RULES = {
  internalAccrualHold: false,
  supportsPvReversal: true,
  supportsBonusReversal: true,
  supportsWithdrawalBlock: true,
  supportsAccountBlock: true,
  debtIsSeparateFromAvailableBalance: true,
  futureRewardsRepayDebtFirst: true,
} as const;

export const WITHDRAWAL_RULES = {
  asset: "USDT",
  minimumUsd: 100,
  feePaidByUser: true,
  targetMode: "automatic",
  network: null,
  fee: null,
  processingTime: null,
  limits: null,
  verification: null,
} as const;

export const INTERNAL_TRANSFER_RULES = {
  featureRequired: true,
  transferableBalance: null,
  receivedFundsWithdrawable: null,
  minimum: null,
  maximum: null,
  fee: null,
  limits: null,
  reversible: null,
  verification: null,
} as const;

export const OPEN_MARKETING_DECISIONS = [
  "Статусная премия: real-time начисление конфликтует с правилом одной максимальной премии недели.",
  "PV-маршрут через неактивные позиции и запрет либо отсутствие компрессии.",
  "Участие апгрейда приглашённого в быстром старте.",
  "Точный алгоритм автоматического бинарного размещения.",
  "Статусная квалификация приглашённых, пришедших во время неактивности.",
  "Отмена исторического статуса после fraud или chargeback.",
  "Сеть, комиссия, SLA, лимиты, KYC и 2FA для вывода USDT.",
  "Правила внутренних переводов.",
  "Продуктовый состав тарифов, курсов, токенов и Marketplace.",
  "Календарная модель продления: месяц или фиксированное число дней, границы и раннее продление.",
  "Точность и округление бинарного дохода и матчинга.",
  "Цена апгрейда и влияние апгрейда на период активности.",
] as const;

export const CURRENT_DEMO_TIER = PARTNER_TIERS[1];

export function getPartnerTier(tierId: PartnerTierId): PartnerTier {
  const tier = PARTNER_TIERS.find((item) => item.id === tierId);
  if (!tier) throw new Error(`Unknown partner tier: ${tierId}`);
  return tier;
}

/** Direct sponsor cash + own PV eligibility for a new package purchase. */
export function calculateDirectPurchaseReward(
  sponsorTierId: PartnerTierId,
  purchasedTierId: PartnerTierId,
  activityState: PartnerActivityState,
): PurchaseReward {
  if (activityState === "inactive_without_plan") return { cashUsd: 0, pv: 0 };
  const approved = PERSONAL_REWARD_MATRIX[sponsorTierId][purchasedTierId];
  return {
    cashUsd: approved.cashUsd,
    pv: activityState === "active" ? approved.pv : 0,
  };
}

/** Purchase PV for any physical upline. Cash is never propagated by this function. */
export function calculatePurchasePvForUpline(
  receiverTierId: PartnerTierId,
  purchasedTierId: PartnerTierId,
  physicalLevel: number,
  isReceiverActive: boolean,
): number {
  if (!isReceiverActive || !Number.isInteger(physicalLevel) || physicalLevel < 1) return 0;
  const receiverTier = getPartnerTier(receiverTierId);
  const purchasedTier = getPartnerTier(purchasedTierId);
  if (physicalLevel > receiverTier.binaryDepth) return 0;
  return Math.min(receiverTier.purchasePvCap, purchasedTier.purchasePvCap);
}

/** Owner-approved 3/9/15 subscription-PV rule; no global nine-level cap. */
export function calculateSubscriptionPvForUpline(
  receiverTierId: PartnerTierId,
  physicalLevel: number,
  isReceiverActive: boolean,
): number {
  if (!isReceiverActive || !Number.isInteger(physicalLevel) || physicalLevel < 1) return 0;
  return physicalLevel <= SUBSCRIPTION_RULES.pvDepthByTier[receiverTierId]
    ? SUBSCRIPTION_RULES.generatedPv
    : 0;
}

export function calculateDirectSubscriptionReward(isDirectSponsorActive: boolean): number {
  return isDirectSponsorActive ? SUBSCRIPTION_RULES.directSponsorRewardUsd : 0;
}

export type UpgradePath = keyof typeof UPGRADE_REWARD_MATRIX;

/** Approved upgrade differential; upgrade price and activity-period effects remain open. */
export function calculateUpgradeReward(
  path: UpgradePath,
  sponsorTierId: PartnerTierId,
  activityState: PartnerActivityState,
): PurchaseReward {
  if (activityState === "inactive_without_plan") return { cashUsd: 0, pv: 0 };
  const approved = UPGRADE_REWARD_MATRIX[path][sponsorTierId];
  return {
    cashUsd: approved.cashUsd,
    pv: activityState === "active" ? approved.pv : 0,
  };
}

/** Preview only: final precision and rounding still require an owner decision. */
export function calculateBinaryPreview(leftPv: number, rightPv: number) {
  const safeLeft = Math.max(0, leftPv);
  const safeRight = Math.max(0, rightPv);
  const collapsedPv = Math.min(safeLeft, safeRight);
  return {
    collapsedPv,
    unroundedIncomeUsd: collapsedPv / BINARY_RULES.collapsedPvPerUsd,
    leftRemainderPv: safeLeft - collapsedPv,
    rightRemainderPv: safeRight - collapsedPv,
  };
}

export function calculateMatchingPreview(
  receiverTierId: PartnerTierId,
  sponsorLine: number,
  downlineBinaryIncomeUsd: number,
  isReceiverActive: boolean,
): number {
  if (!isReceiverActive || !Number.isInteger(sponsorLine) || sponsorLine < 1 || sponsorLine > MATCHING_RULES.sponsorLinesByTier[receiverTierId]) return 0;
  return Math.max(0, downlineBinaryIncomeUsd) * (MATCHING_RULES.percentOfBinaryIncome / 100);
}
