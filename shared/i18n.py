"""پیام‌های چندزبانه (فارسی / انگلیسی / عربی) مطابق R-GEN-04."""
from __future__ import annotations

MESSAGES: dict[str, dict[str, str]] = {
    "command_center_title": {
        "fa": "مرکز فرماندهی زنجیره ارزش",
        "en": "Value Chain Command Center",
        "ar": "مركز قيادة سلسلة القيمة",
    },
    "brand": {
        "fa": "هلدینگ خلیج فارس",
        "en": "Persian Gulf Holding",
        "ar": "مجموعة الخليج الفارسي",
    },
    "optimization_complete": {
        "fa": "بهینه‌سازی یکپارچه با موفقیت انجام شد",
        "en": "Integrated optimization completed successfully",
        "ar": "اكتملت عملية التحسين المتكاملة بنجاح",
    },
    "unauthorized": {
        "fa": "دسترسی غیرمجاز",
        "en": "Unauthorized",
        "ar": "غير مصرح",
    },
    "nav_dashboard": {"fa": "داشبورد", "en": "Dashboard", "ar": "لوحة القيادة"},
    "nav_cost": {"fa": "هزینه و حاشیه", "en": "Cost & Margin", "ar": "التكلفة والهامش"},
    "nav_distribution": {"fa": "عملکرد توزیع", "en": "Distribution", "ar": "الأداء اللوجستي"},
    "nav_alerts": {"fa": "هشدارها", "en": "Alerts", "ar": "التنبيهات"},
    "nav_optimize": {"fa": "بهینه‌سازی", "en": "Optimization", "ar": "التحسين"},
    "filter_subsidiary": {"fa": "شرکت تابعه", "en": "Subsidiary", "ar": "الشركة التابعة"},
    "filter_product": {"fa": "محصول", "en": "Product", "ar": "المنتج"},
    "filter_region": {"fa": "منطقه", "en": "Region", "ar": "المنطقة"},
    "filter_period": {"fa": "بازه زمانی", "en": "Period", "ar": "الفترة"},
    "kpi_otif": {"fa": "تحویل به‌موقع (OTIF)", "en": "On-Time In-Full", "ar": "التسليم في الوقت"},
    "kpi_fill": {"fa": "پرشدگی انبار", "en": "Warehouse Fill", "ar": "امتلاء المستودع"},
    "kpi_margin": {"fa": "حاشیه عملیاتی", "en": "Operating Margin", "ar": "هامش التشغيل"},
    "kpi_orders": {"fa": "سفارشات امروز", "en": "Orders Today", "ar": "طلبات اليوم"},
    "kpi_ships": {"fa": "کشتی در بندر", "en": "Ships in Port", "ar": "السفن في الميناء"},
    "kpi_eta": {"fa": "میانگین ETA (روز)", "en": "Avg ETA (days)", "ar": "متوسط الوصول"},
    "cost_per_ton": {"fa": "هزینه تمام‌شده هر تن", "en": "Cost per Ton", "ar": "التكلفة للطن"},
    "margin_per_unit": {"fa": "حاشیه سود واحد", "en": "Unit Margin", "ar": "هامش الوحدة"},
    "alerts_title": {"fa": "هشدارهای هوشمند", "en": "Smart Alerts", "ar": "تنبيهات ذكية"},
    "run_budget_check": {"fa": "بررسی انحراف بودجه", "en": "Run Budget Check", "ar": "فحص انحراف الميزانية"},
    "acknowledge": {"fa": "تأیید", "en": "Acknowledge", "ar": "إقرار"},
    "login": {"fa": "ورود", "en": "Sign in", "ar": "تسجيل الدخول"},
    "role_executive": {"fa": "مدیر ارشد", "en": "Executive", "ar": "تنفيذي"},
    "role_analyst": {"fa": "تحلیل‌گر", "en": "Analyst", "ar": "محلل"},
    "role_logistics": {"fa": "لجستیک", "en": "Logistics", "ar": "اللوجستيات"},
    "role_sales": {"fa": "فروش", "en": "Sales", "ar": "المبيعات"},
    "no_alerts": {"fa": "هشدار فعالی نیست", "en": "No active alerts", "ar": "لا توجد تنبيهات"},
    "period_7d": {"fa": "۷ روز", "en": "7 days", "ar": "٧ أيام"},
    "period_30d": {"fa": "۳۰ روز", "en": "30 days", "ar": "٣٠ يوماً"},
    "period_90d": {"fa": "۹۰ روز", "en": "90 days", "ar": "٩٠ يوماً"},
    "all": {"fa": "همه", "en": "All", "ar": "الكل"},
}


def t(key: str, locale: str = "fa") -> str:
    entry = MESSAGES.get(key, {})
    return entry.get(locale) or entry.get("en") or key


def bundle(locale: str = "fa") -> dict[str, str]:
    return {k: t(k, locale) for k in MESSAGES}
