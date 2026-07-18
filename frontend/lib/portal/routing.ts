import type { MarketOffer, MarketTab, SectionId, TFn } from "./types";
import { accessPackages, marketPrograms, tokenPacks } from "./mock-data";

export const routeBySection: Partial<Record<SectionId, string>> = {
  home: "/",
  cabinet: "/cabinet",
  crm: "/crm",
  partners: "/team",
  wallet: "/finance",
  courses: "/courses",
  library: "/materials",
  marketplace: "/market/packages",
  profile: "/profile",
  labor: "/labor",
  chats: "/chats",
  marketing: "/chats",
};

export const sectionIds = new Set<SectionId>([
  "home",
  "cabinet",
  "workspace",
  "courses",
  "library",
  "labor",
  "chats",
  "marketing",
  "partners",
  "crm",
  "marketplace",
  "wallet",
  "profile",
]);

export function routeSlug(value: string) {
  const transliteration: Record<string, string> = {
    а: "a", б: "b", в: "v", г: "g", д: "d", е: "e", ё: "e", ж: "zh", з: "z", и: "i", й: "y",
    к: "k", л: "l", м: "m", н: "n", о: "o", п: "p", р: "r", с: "s", т: "t", у: "u", ф: "f",
    х: "h", ц: "ts", ч: "ch", ш: "sh", щ: "sch", ъ: "", ы: "y", ь: "", э: "e", ю: "yu", я: "ya",
  };

  return value
    .trim()
    .toLowerCase()
    .split("")
    .map((character) => transliteration[character] ?? character)
    .join("")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export function matchesRoute(pathname: string, route: string) {
  return pathname === route || pathname.startsWith(`${route}/`);
}

export function sectionFromPathname(pathname: string): SectionId | null {
  if (pathname === "/") return "home";
  if (pathname === "/cabinet") return "cabinet";
  if (matchesRoute(pathname, "/team")) return "partners";
  if (matchesRoute(pathname, "/crm")) return "crm";
  if (matchesRoute(pathname, "/finance")) return "wallet";
  if (matchesRoute(pathname, "/cabinet/crm")) return "crm";
  if (matchesRoute(pathname, "/cabinet/structure")) return "partners";
  if (matchesRoute(pathname, "/cabinet/wallet")) return "wallet";
  if (matchesRoute(pathname, "/courses")) return "courses";
  if (matchesRoute(pathname, "/materials")) return "library";
  if (matchesRoute(pathname, "/marketing")) return "chats";
  if (matchesRoute(pathname, "/market")) return "marketplace";
  if (matchesRoute(pathname, "/profile")) return "profile";
  if (matchesRoute(pathname, "/labor")) return "labor";
  if (matchesRoute(pathname, "/chats")) return "chats";
  return null;
}

export function marketTabFromPathname(pathname: string): MarketTab | null {
  if (matchesRoute(pathname, "/market/packages")) return "packages";
  if (matchesRoute(pathname, "/market/tokens")) return "tokens";
  if (matchesRoute(pathname, "/market")) return "packages";
  return null;
}

export function marketOfferFromPathname(pathname: string): MarketOffer | null {
  const match = pathname.match(/^\/market\/(programs|packages|tokens)\/([^/]+)$/);
  if (!match) return null;
  const [, group, slug] = match;

  if (group === "programs") {
    const item = marketPrograms.find((program) => routeSlug(program.title) === slug);
    return item ? {
      kind: "program",
      title: item.title,
      price: item.price,
      pv: item.pv,
      text: item.text,
      features: ["Состав, цена, PV и условия доступа находятся в проработке"],
    } : null;
  }

  if (group === "packages") {
    const item = accessPackages.find((marketPackage) => routeSlug(marketPackage.title) === slug);
    return item ? {
      kind: "package",
      title: item.title,
      price: item.price,
      pv: item.pv,
      text: item.text,
      features: item.features,
    } : null;
  }

  const item = tokenPacks.find((tokenPack) => routeSlug(tokenPack.title) === slug);
  return item ? {
    kind: "tokens",
    title: item.title,
    price: item.price,
    pv: item.pv,
    text: item.text,
    features: [
      "Токены зачисляются на баланс AI Hub",
      "Не участвуют в PV и партнёрских начислениях",
    ],
    productId: slug.includes("5000") ? "tokens-5000" : "tokens-1000",
  } : null;
}

export function marketOfferHref(offer: MarketOffer) {
  const group = offer.kind === "program" ? "programs" : offer.kind === "package" ? "packages" : "tokens";
  return `/market/${group}/${routeSlug(offer.title)}`;
}

export function sectionHref(section: SectionId) {
  const sectionRoute = routeBySection[section];
  if (sectionRoute) return sectionRoute;
  return `/?section=${section}`;
}

export function pageTitle(active: SectionId, t: TFn) {
  const titles: Record<SectionId, string> = {
    home: "Главная",
    cabinet: "Кабинет",
    workspace: "AI Hub",
    courses: "Академия",
    library: "Материалы",
    labor: "Биржа труда",
    chats: "Чаты",
    marketing: "Канал маркетинга",
    partners: "Команда",
    crm: "CRM",
    marketplace: "Маркет",
    wallet: "Финансы",
    profile: "Профиль",
  };
  return t(titles[active]);
}
