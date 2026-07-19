# Бизнес-константы (единый источник; seed и формулы читают из БД где возможно)
ACTIVITY_DAYS_PER_MONTH = 30
RENEWAL_WINDOW_DAYS = 0  # 0 = продление всегда; >0 = окно N дней до конца активности
MATCHING_PERCENT = 10
QUICK_START_LABEL = "4 личных Pro/Max · 30 дней · $90"

# Fallback до загрузки TariffPlan из БД (тесты без seed)
TARIFF_RANK_FALLBACK = {
    "rise": 1,
    "rise-pro": 2,
    "rise-pro-max": 3,
}
