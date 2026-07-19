"use client";

import {
  Bot,
  BriefcaseBusiness,
  Brush,
  Camera,
  CircleUserRound,
  FileText,
  Home,
  Images,
  Library,
  MessageSquareText,
  MessagesSquare,
  Play,
  Rocket,
  ShoppingBag,
  Sparkles,
  SquareKanban,
  Users,
  Video,
  WandSparkles,
  WalletCards,
  Workflow,
} from "lucide-react";
import { PARTNER_TIERS, QUICK_START_RULES } from "../marketing-plan";
import type { CourseModuleItem, CrmColumn, SectionId, TeamPartnerNode } from "./types";

export const navItems: Array<{ id: SectionId; label: string; icon: typeof Home }> = [
  { id: "home", label: "Главная", icon: Home },
  { id: "cabinet", label: "Кабинет", icon: BriefcaseBusiness },
  { id: "crm", label: "CRM", icon: SquareKanban },
  { id: "wallet", label: "Финансы", icon: WalletCards },
  { id: "workspace", label: "AI Hub", icon: Sparkles },
  { id: "library", label: "Материалы", icon: Library },
  { id: "chats", label: "Чаты", icon: MessagesSquare },
  { id: "marketplace", label: "Маркет", icon: ShoppingBag },
  { id: "profile", label: "Профиль", icon: CircleUserRound },
];

export const mobileLabels: Record<SectionId, string> = {
  home: "Главная",
  cabinet: "Кабинет",
  workspace: "AI",
  courses: "Академия",
  library: "База",
  chats: "Чаты",
  marketing: "Маркетинг",
  partners: "Команда",
  crm: "CRM",
  marketplace: "Маркет",
  wallet: "Финансы",
  profile: "Профиль",
};

export const mobileNavIds: SectionId[] = ["home", "workspace", "marketplace", "profile"];
export const mobileMoreIds: SectionId[] = ["cabinet", "crm", "wallet", "library", "chats"];

export const courses = [
  {
    title: "ChatGPT с нуля",
    subtitle: "Научитесь писать запросы, получать сильные ответы и применять GPT в работе",
    progress: 100,
    color: "blue",
    icon: MessageSquareText,
    lessons: 21,
  },
  {
    title: "Дизайн с нейросетями",
    subtitle: "Создавайте обложки, баннеры, карточки и визуалы без сложных программ",
    progress: 54,
    color: "violet",
    icon: Brush,
    lessons: 18,
  },
  {
    title: "AI-видео и Reels",
    subtitle: "Делайте короткие ролики, сценарии, озвучку и визуальные сцены",
    progress: 42,
    color: "cyan",
    icon: Video,
    lessons: 16,
  },
  {
    title: "Промпты для бизнеса",
    subtitle: "Готовые формулы запросов для продаж, контента, воронок и сервиса",
    progress: 73,
    color: "purple",
    icon: WandSparkles,
    lessons: 24,
  },
  {
    title: "Автоматизация задач",
    subtitle: "Собирайте AI-процессы для рутины, контента, заявок и команды",
    progress: 61,
    color: "green",
    icon: Workflow,
    lessons: 19,
  },
  {
    title: "Личный бренд и контент",
    subtitle: "Упакуйте экспертность, контент-план, сторителлинг и монетизацию",
    progress: 37,
    color: "orange",
    icon: Rocket,
    lessons: 15,
  },
  {
    title: "AI-фотосессии",
    subtitle: "Генерируйте портреты, рекламные кадры и образы для соцсетей",
    progress: 18,
    color: "cyan",
    icon: Camera,
    lessons: 14,
  },
  {
    title: "Дизайн без Photoshop",
    subtitle: "Логотипы, презентации, карточки, афиши и быстрые правки через AI",
    progress: 0,
    color: "violet",
    icon: Images,
    lessons: 12,
  },
  {
    title: "Женские фотосессии",
    subtitle: "Промпты для образов, портретов, fashion-съемок и личного бренда",
    progress: 0,
    color: "purple",
    icon: Camera,
    lessons: 10,
  },
  {
    title: "Мужские фотосессии",
    subtitle: "Промпты для деловых, lifestyle, fashion и экспертных образов",
    progress: 0,
    color: "blue",
    icon: Camera,
    lessons: 10,
  },
  {
    title: "AI-мультфильмы",
    subtitle: "Создавайте персонажей, мини-сюжеты и короткие анимационные ролики",
    progress: 12,
    color: "green",
    icon: Sparkles,
    lessons: 13,
  },
  {
    title: "Партнерские продажи",
    subtitle: "Научитесь приглашать, прогревать аудиторию и развивать команду",
    progress: 25,
    color: "orange",
    icon: Users,
    lessons: 11,
  },
];

export const accessPackages = PARTNER_TIERS.map((tier, index) => ({
  title: tier.name,
  eyebrow: index === 0 ? "Входной тариф" : index === 1 ? "Расширенный тариф" : "Максимальный тариф",
  text: `Партнёрский тариф с физической PV-глубиной ${tier.binaryDepth} уровней и матчингом на ${tier.matchingLines} спонсорских линиях.`,
  price: `$${tier.priceUsd}`,
  pv: `до ${tier.purchasePvCap} PV активному получателю`,
  note: tier.quickStartEligible
    ? `${QUICK_START_RULES.requiredPersonalPartners} личных Pro/Max · ${QUICK_START_RULES.windowDays} дней с первой покупки · $${QUICK_START_RULES.rewardUsd}`
    : "Первый месяц партнёрской активности включён",
  highlight: index === 1,
  features: [
    `Личный бонус прямому пригласившему: до $${tier.personalBonusCapUsd}`,
    `PV активному вышестоящему: до ${tier.purchasePvCap}`,
    `Бинарная глубина: ${tier.binaryDepth} уровней`,
    `Матчинг: 10% · ${tier.matchingLines} ${tier.matchingLines === 1 ? "линия" : "линии"}`,
  ],
}));

export const marketPrograms = [
  { title: "GPT - NEW", text: "ChatGPT с нуля: запросы, роли, структура ответов и ежедневная работа с AI", price: "Не утверждено", pv: "PV не утверждён", icon: MessageSquareText, color: "cyan", badge: "NEW" },
  { title: "NANO BANANA", text: "Дизайн-задачи без Photoshop: логотипы, карточки, баннеры и визуалы для продаж", price: "Не утверждено", pv: "PV не утверждён", icon: Brush, color: "orange", badge: "HIT" },
  { title: "AI - мультики NEW", text: "Создавайте мультсериалы, короткие AI-ролики, Reels-сцены и вирусный видеоконтент", price: "Не утверждено", pv: "PV не утверждён", icon: Video, color: "purple", badge: "TOP" },
  { title: "AI ФОТОГРАФ", text: "Профессиональные AI-фотосессии, портреты, рекламные кадры и визуалы для соцсетей", price: "Не утверждено", pv: "PV не утверждён", icon: Camera, color: "blue", badge: "NEW" },
  { title: "CLAUDE", text: "Делегируйте рутину AI: документы, тексты, анализ, структуры и рабочие сценарии", price: "Не утверждено", pv: "PV не утверждён", icon: Workflow, color: "violet", badge: "18+" },
  { title: "НОВЫЙ БЛОГИНГ", text: "Практическая система блога: упаковка, контент-план, сторителлинг и монетизация", price: "Не утверждено", pv: "PV не утверждён", icon: Rocket, color: "violet", badge: "TOP" },
  { title: "MIDJOURNEY", text: "Освойте Midjourney с нуля: стили, сцены, промпты и стабильная генерация визуалов", price: "Не утверждено", pv: "PV не утверждён", icon: Images, color: "purple", badge: "HIT" },
  { title: "Партнерские продажи", text: "Приглашения, прогрев, встречи и рост партнерской команды", price: "Не утверждено", pv: "PV не утверждён", icon: Users, color: "green", badge: "RE:RISE" },
  { title: "PROMTS WOMAN", text: "Библиотека промптов для генерации женских фотосессий, образов и визуальных серий", price: "Не утверждено", pv: "PV не утверждён", icon: WandSparkles, color: "violet", badge: "NEW" },
  { title: "PROMTS MAN", text: "Библиотека промптов для мужских фотосессий, портретов и деловых визуалов", price: "Не утверждено", pv: "PV не утверждён", icon: WandSparkles, color: "blue" },
  { title: "PROMTS KIDS", text: "Промпты для детских фотосессий, семейных кадров, сторис и мягких визуальных сцен", price: "Не утверждено", pv: "PV не утверждён", icon: WandSparkles, color: "green" },
  { title: "PROMTS LOVE", text: "Промпты для парных фотосессий, романтических сцен и визуалов для love-story", price: "Не утверждено", pv: "PV не утверждён", icon: WandSparkles, color: "orange" },
];

export const marketProgramCourseMap: Record<string, string> = {
  "NANO BANANA": "Дизайн без Photoshop",
  "AI ФОТОГРАФ": "AI-фотосессии",
  "НОВЫЙ БЛОГИНГ": "Личный бренд и контент",
  MIDJOURNEY: "Дизайн с нейросетями",
  "PROMTS WOMAN": "Женские фотосессии",
  "PROMTS MAN": "Мужские фотосессии",
  "GPT - NEW": "ChatGPT с нуля",
  "AI - мультики NEW": "AI-мультфильмы",
  "Партнерские продажи": "Партнерские продажи",
};

export const tokenPacks = [
  {
    title: "1000 токенов",
    text: "1000 токенов AI Hub · 100 ток./$1",
    price: "$10",
    pv: "без PV",
  },
  {
    title: "5000 токенов",
    text: "5000 токенов AI Hub · 125 ток./$1",
    price: "$40",
    pv: "без PV",
  },
];

export const materialCards = [
  {
    title: "Промпты",
    text: "Готовые формулы для ChatGPT, продаж, контента, сервиса и упаковки продукта.",
    count: 64,
    updated: "Сегодня",
    category: "AI Hub",
    kind: "PROMPT",
    color: "blue",
    icon: MessageSquareText,
  },
  {
    title: "Презентации",
    text: "Слайды для встреч, демо платформы, партнерских созвонов и презентаций.",
    count: 18,
    updated: "Сегодня",
    category: "Продажи",
    kind: "PDF",
    color: "violet",
    icon: Images,
  },
  {
    title: "Скрипты продаж",
    text: "Сообщения для приглашений, прогрева, follow-up и закрытия на оплату.",
    count: 42,
    updated: "Вчера",
    category: "Продажи",
    kind: "DOC",
    color: "cyan",
    icon: MessageSquareText,
  },
  {
    title: "Reels-сценарии",
    text: "Сценарии коротких видео, hooks, структуры роликов и контент-планы.",
    count: 31,
    updated: "Сегодня",
    category: "Контент",
    kind: "VIDEO",
    color: "orange",
    icon: Play,
  },
  {
    title: "Документы",
    text: "Чек-листы, договоренности, инструкции, регламенты и материалы для команды.",
    count: 27,
    updated: "2 дня назад",
    category: "Документы",
    kind: "PDF",
    color: "purple",
    icon: FileText,
  },
  {
    title: "AI-воронки",
    text: "Связки промптов, сообщений и материалов под разные сценарии продаж.",
    count: 12,
    updated: "Сегодня",
    category: "AI Hub",
    kind: "FLOW",
    color: "green",
    icon: Workflow,
  },
  {
    title: "CRM-шаблоны",
    text: "Карточки лидов, этапы воронки, задачи, заметки и шаблоны сопровождения.",
    count: 16,
    updated: "Вчера",
    category: "CRM",
    kind: "TEMPLATE",
    color: "blue",
    icon: SquareKanban,
  },
  {
    title: "Партнерские материалы",
    text: "Офферы, возражения и короткие материалы для партнерских встреч.",
    count: 35,
    updated: "Сегодня",
    category: "Партнёрские",
    kind: "KIT",
    color: "violet",
    icon: Users,
  },
];

export const promoBanners = [
  {
    eyebrow: "Prestart",
    title: "1 августа",
    text: "Первые участники заходят в проект, получают ранний доступ и начинают знакомство с платформой.",
    theme: "ai",
    icon: Rocket,
    image: "/assets/portal/home-banner-prestart.webp",
  },
  {
    eyebrow: "RE:RISE",
    title: "2 часть ChatGPT",
    text: "Продвинутые сценарии, сильные промпты и рабочие связки для контента, продаж и автоматизации.",
    theme: "ai",
    icon: Sparkles,
    image: "/assets/portal/home-banner-chatgpt-part-2.webp",
  },
  {
    eyebrow: "Новая программа",
    title: "Claude",
    text: "Освойте Claude для сильных текстов, аналитики и продвинутых рабочих сценариев.",
    theme: "academy",
    icon: Bot,
    image: "/assets/portal/home-banner-claude.webp",
  },
  {
    eyebrow: "RE:RISE",
    title: "Чат партнёров",
    text: "Комьюнити для тех, кто строит команду, продажи и личный бренд.",
    theme: "crm",
    icon: MessageSquareText,
    image: "/assets/portal/home-banner-partner-chat.webp",
  },
];

export const crmColumns: CrmColumn[] = [
  {
    id: "new",
    title: "Новые лиды",
    color: "blue",
    deals: [
      { id: "lead-marina", name: "Марина К.", source: "Instagram", task: "Новая заявка", time: "Сегодня в 15:00", phone: "+7 900 214-55-11", contact: "@marina.ai", note: "Интересуется AI Hub для контента и личного бренда." },
      { id: "lead-ilya", name: "Илья С.", source: "Рекомендация", task: "Теплый контакт", time: "Завтра", phone: "+7 916 402-18-77", contact: "@ilya_growth", note: "Пришел по рекомендации, нужно объяснить различия пакетов Rise и Rise Pro." },
      { id: "lead-viktor", name: "Виктор Л.", source: "YouTube", task: "Проверить запрос", time: "Сегодня", phone: "+7 903 118-72-40", contact: "@viktor_ai", note: "Оставил заявку после ролика про автоматизацию продаж." },
      { id: "lead-alina", name: "Алина Т.", source: "VK", task: "Написать в личку", time: "Сегодня", phone: "+7 926 401-19-33", contact: "@alina.brand", note: "Нужны сценарии для упаковки экспертного блога." },
      { id: "lead-sergey", name: "Сергей Б.", source: "Партнер", task: "Уточнить цель", time: "Завтра", phone: "+7 915 640-82-11", contact: "@sergey_rerise", note: "Партнер привел предпринимателя, интерес к команде и CRM." },
      { id: "lead-natalia", name: "Наталья В.", source: "Сайт", task: "Отправить обзор", time: "Через 3 часа", phone: "+7 911 704-28-50", contact: "@natalia.flow", note: "Просит короткий обзор возможностей AI Hub для отдела контента." },
      { id: "lead-timur", name: "Тимур Г.", source: "Telegram Ads", task: "Квалифицировать", time: "Сегодня", phone: "+7 999 832-16-05", contact: "@timur_sales", note: "Хочет понять тарифы и лимиты токенов перед подключением." },
    ],
  },
  {
    id: "contact",
    title: "Связаться",
    color: "green",
    deals: [
      { id: "lead-anton", name: "Антон Р.", source: "Telegram", task: "Назначить звонок", time: "Через 2 часа", phone: "+7 925 318-60-44", contact: "@anton_reels", note: "Хочет понять, как быстро запустить продажи через Reels." },
      { id: "lead-olga", name: "Ольга М.", source: "Чат партнеров", task: "Созвон сегодня", time: "Сегодня в 15:00", phone: "+7 921 777-34-02", contact: "@olga_meta", note: "Уже смотрела презентацию, нужно закрыть вопросы по подписке Rise." },
      { id: "lead-pavel", name: "Павел Д.", source: "Личная ссылка", task: "Дожать ответ", time: "Сегодня", phone: "+7 916 548-90-12", contact: "@pavel_digit", note: "Получил презентацию, ждёт сравнение Rise и Rise Pro." },
      { id: "lead-ekaterina", name: "Екатерина С.", source: "Instagram", task: "Назначить демо", time: "Завтра", phone: "+7 925 441-62-80", contact: "@katya.content", note: "Интересуется промптами и материалами для запуска личного бренда." },
      { id: "lead-mikhail", name: "Михаил Ф.", source: "Вебинар", task: "Отправить слоты", time: "Через 4 часа", phone: "+7 911 603-77-24", contact: "@mikhail_launch", note: "После вебинара попросил варианты времени для короткого созвона." },
    ],
  },
  {
    id: "meeting",
    title: "Встреча",
    color: "orange",
    deals: [
      { id: "lead-dmitry", name: "Дмитрий Н.", source: "Личная ссылка", task: "Демо продукта", time: "Завтра", phone: "+7 999 404-12-88", contact: "@dmitry_n", note: "Назначена демонстрация back office и CRM." },
      { id: "lead-karina", name: "Карина В.", source: "Reels", task: "Отправить запись", time: "Просрочено", phone: "+7 903 552-20-19", contact: "@karina.visual", note: "Нужно повторно отправить запись вебинара и спросить обратную связь." },
      { id: "lead-arseniy", name: "Арсений К.", source: "Telegram", task: "Провести Zoom", time: "Сегодня в 18:00", phone: "+7 900 672-43-18", contact: "@arseniy_ai", note: "Встреча по сценарию запуска партнерской ветки." },
    ],
  },
  {
    id: "deal",
    title: "Сделка",
    color: "violet",
    deals: [
      { id: "lead-roman", name: "Роман П.", source: "Встреча Zoom", task: "Обсудить пакет", time: "Сегодня в 15:00", phone: "+7 911 221-45-90", contact: "@roman_partner", note: "Выбирает между Rise и Rise Pro, важен полный доступ к программам." },
      { id: "lead-elena", name: "Елена А.", source: "Наставник", task: "Оплата", time: "Через 2 часа", phone: "+7 926 887-41-12", contact: "@elena_rerise", note: "Готова оплатить Rise Pro, нужно отправить ссылку и сопроводить оплату." },
    ],
  },
];

export const chatGptCurriculum: CourseModuleItem[] = [
  {
    title: "Тестовый материал",
    description: "Короткие вводные уроки и практическое применение ChatGPT в повседневной жизни.",
    lessons: [
      { title: "Основы ChatGPT", duration: "14 мин" },
      { title: "Как оплатить нейросети?", duration: "12 мин" },
      { title: "Практическое применение ChatGPT в жизни", duration: "18 мин" },
      { title: "Эффективное использование ChatGPT в повседневной жизни", duration: "20 мин" },
    ],
  },
  {
    title: "Знакомство с ChatGPT",
    description: "Изучаем возможности интерфейса и учимся управлять результатом через промпты.",
    lessons: [
      { title: "Как работать с ChatGPT — возможности чата и интерфейс", duration: "22 мин" },
      { title: "Промптинг: как управлять результатом", duration: "24 мин" },
    ],
  },
  {
    title: "Полиграфия — создание коммерческого дизайна",
    description: "Создаём коммерческие визуалы, которые можно упаковать в услугу или продукт.",
    lessons: [
      { title: "Паттерны и текстуры", duration: "18 мин" },
      { title: "Наклейки и этикетки — часть 1", duration: "20 мин" },
      { title: "Наклейки и этикетки — часть 2", duration: "21 мин" },
      { title: "Дизайн упаковки и мокапов — визуализация бренда", duration: "27 мин" },
      { title: "Дизайн для Print-on-demand", duration: "23 мин" },
    ],
  },
  {
    title: "Сезонный контент — как монетизировать тренды и праздники",
    description: "Находим сезонные идеи и превращаем их в актуальный коммерческий продукт.",
    lessons: [
      { title: "Как находить визуальные тренды и сезонные стили", duration: "24 мин" },
      { title: "Как формировать дизайн-концепцию под праздники и продукт", duration: "29 мин" },
      { title: "Как упаковать сезонный дизайн в продаваемый продукт", duration: "21 мин" },
    ],
  },
  {
    title: "Образовательный контент — как превращать знания в продукт",
    description: "Проектируем полезные материалы и собираем из знаний самостоятельный продукт.",
    lessons: [
      { title: "Как превращать знания в обучающий контент", duration: "26 мин" },
      { title: "Как создавать обучающие материалы — теория", duration: "25 мин" },
      { title: "Как создавать обучающие материалы — практика", duration: "28 мин" },
      { title: "Как визуализировать обучение", duration: "24 мин" },
    ],
  },
  {
    title: "Персонализированный контент",
    description: "Создаём персональные изображения под конкретный коммерческий запрос.",
    lessons: [
      { title: "Как создавать персонализированные изображения: портреты, карикатуры, постеры и аватары", duration: "27 мин" },
      { title: "Как разрабатывать изображения под персонализированный коммерческий запрос", duration: "31 мин" },
      { title: "Как выполнять заказы быстро и стабильно: техническое задание, стиль и шаблоны", duration: "36 мин" },
    ],
  },
];

export const courseTopicSeeds: Record<string, string[]> = {
  "Дизайн с нейросетями": ["визуальная идея", "референсы и стили", "композиция", "типографика", "баннеры", "карточки продукта", "серия визуалов", "финальный макет"],
  "AI-видео и Reels": ["идея ролика", "сценарий", "раскадровка", "генерация сцен", "озвучка", "монтаж", "субтитры", "публикация"],
  "Промпты для бизнеса": ["задачи бизнеса", "формула промпта", "продажи", "маркетинг", "сервис", "аналитика", "команда", "библиотека запросов"],
  "Автоматизация задач": ["карта процессов", "поиск рутины", "AI-инструменты", "связки сервисов", "контент-процесс", "обработка заявок", "контроль качества", "внедрение"],
  "Личный бренд и контент": ["позиционирование", "аудитория", "контент-опоры", "сторителлинг", "контент-план", "визуальный стиль", "воронка", "система публикаций"],
  "AI-фотосессии": ["концепция съёмки", "подбор референсов", "описание героя", "свет и ракурс", "стилизация", "серия кадров", "ретушь", "портфолио"],
  "Дизайн без Photoshop": ["основа макета", "логотип", "презентация", "карточка", "афиша", "правки", "экспорт", "итоговый набор"],
  "Женские фотосессии": ["концепция образа", "портрет", "beauty", "fashion", "локация", "свет", "серия кадров", "личный бренд"],
  "Мужские фотосессии": ["деловой образ", "экспертный портрет", "lifestyle", "fashion", "локация", "свет", "серия кадров", "личный бренд"],
  "AI-мультфильмы": ["идея истории", "герой", "визуальный стиль", "сценарий", "сцены", "анимация", "звук", "финальный ролик"],
  "Партнерские продажи": ["позиционирование", "поиск контактов", "первое сообщение", "квалификация", "презентация", "возражения", "сделка", "сопровождение"],
};

export const TEAM_PARTNER_DIRECTORY: Record<string, TeamPartnerNode> = {
  andrey: { id: "andrey", name: "Андрей М.", initial: "А", rank: "Партнёр II", sponsorId: null, branchId: "right", level: "L0", active: true, children: ["self", null], teamSize: 284, activeTeam: 91, remainingPv: 0, telegram: "@andrey_rise", phone: "+7 (900) 418-24-10" },
  self: { id: "self", name: "Александр Л.", initial: "R", rank: "Партнёр I", sponsorId: "andrey", branchId: "left", level: "L0", active: true, children: ["maria", "oleg"], teamSize: 176, activeTeam: 53, remainingPv: 340, telegram: "@aleksandr_rise", phone: "+7 (900) 214-55-11" },
  maria: { id: "maria", name: "Мария К.", initial: "М", rank: "Партнёр II", sponsorId: "self", branchId: "left", level: "L1", active: true, children: ["dmitry", "sergey"], teamSize: 98, activeTeam: 31, remainingPv: 340, telegram: "@maria.rise", phone: "+7 (916) 402-18-77" },
  oleg: { id: "oleg", name: "Олег Н.", initial: "О", rank: "Партнёр I", sponsorId: "self", branchId: "right", level: "L1", active: true, children: ["elena", "pavel"], teamSize: 78, activeTeam: 22, remainingPv: 0, telegram: "@oleg.rise", phone: "+7 (925) 118-72-04" },
  dmitry: { id: "dmitry", name: "Дмитрий В.", initial: "Д", rank: "Партнёр I", sponsorId: "self", branchId: "left", level: "L2", active: true, children: ["alina", "viktor"], teamSize: 52, activeTeam: 18, remainingPv: 220, telegram: "@dmitry.rise", phone: "+7 (903) 206-40-18" },
  sergey: { id: "sergey", name: "Сергей Б.", initial: "С", rank: "Партнёр I", sponsorId: "maria", branchId: "right", level: "L2", active: true, children: ["ekaterina", null], teamSize: 45, activeTeam: 13, remainingPv: 120, telegram: "@sergey.rise", phone: "+7 (911) 384-27-60" },
  elena: { id: "elena", name: "Елена Р.", initial: "Е", rank: "Партнёр I", sponsorId: "oleg", branchId: "left", level: "L2", active: true, children: ["anton", "olga"], teamSize: 41, activeTeam: 12, remainingPv: 0, telegram: "@elena.rise", phone: "+7 (926) 518-36-42" },
  pavel: { id: "pavel", name: "Павел Д.", initial: "П", rank: "Партнёр I", sponsorId: "oleg", branchId: "right", level: "L2", active: false, children: [null, null], teamSize: 36, activeTeam: 9, remainingPv: 0, telegram: "@pavel.rise", phone: "+7 (999) 105-48-22" },
  alina: { id: "alina", name: "Алина Т.", initial: "А", rank: "Партнёр I", sponsorId: "dmitry", branchId: "left", level: "L3", active: true, children: [null, null], teamSize: 24, activeTeam: 8, remainingPv: 140, telegram: "@alina.rise", phone: "+7 (901) 224-13-87" },
  viktor: { id: "viktor", name: "Виктор Л.", initial: "В", rank: "Партнёр I", sponsorId: "dmitry", branchId: "right", level: "L3", active: true, children: [null, null], teamSize: 27, activeTeam: 10, remainingPv: 80, telegram: "@viktor.rise", phone: "+7 (905) 668-29-11" },
  ekaterina: { id: "ekaterina", name: "Екатерина С.", initial: "Е", rank: "Партнёр I", sponsorId: "sergey", branchId: "left", level: "L3", active: true, children: [null, null], teamSize: 19, activeTeam: 7, remainingPv: 120, telegram: "@ekaterina.rise", phone: "+7 (909) 771-50-13" },
  anton: { id: "anton", name: "Антон Р.", initial: "А", rank: "Партнёр I", sponsorId: "elena", branchId: "left", level: "L3", active: true, children: [null, null], teamSize: 18, activeTeam: 6, remainingPv: 0, telegram: "@anton.rise", phone: "+7 (977) 408-61-95" },
  olga: { id: "olga", name: "Ольга М.", initial: "О", rank: "Партнёр I", sponsorId: "elena", branchId: "right", level: "L3", active: false, children: [null, null], teamSize: 22, activeTeam: 6, remainingPv: 0, telegram: "@olga.rise", phone: "+7 (915) 632-74-09" },
  anna: { id: "anna", name: "Анна С.", initial: "А", rank: "Партнёр I", sponsorId: "self", branchId: "personal", level: "L1", active: true, children: [null, null], teamSize: 1, activeTeam: 1, remainingPv: 0, telegram: "@anna.rise", phone: "+7 (919) 602-44-18" },
};
