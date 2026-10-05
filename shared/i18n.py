"""Multilingual messages (Persian / English / Arabic) per R-GEN-04."""
from __future__ import annotations

MESSAGES: dict[str, dict[str, str]] = {
    "command_center_title": {
        "fa": "Value Chain Command Center",
        "en": "Value Chain Command Center",
        "ar": "مركز قيادة سلسلة القيمة",
    },
    "brand": {
        "fa": "Persian Gulf Holding",
        "en": "Persian Gulf Holding",
        "ar": "مجموعة الخليج الفارسي",
    },
    "optimization_complete": {
        "fa": "The integrated optimization completed successfully",
        "en": "Integrated optimization completed successfully",
        "ar": "اكتملت عملية التحسين المتكاملة بنجاح",
    },
    "unauthorized": {
        "fa": "Unauthorized access",
        "en": "Unauthorized",
        "ar": "غير مصرح",
    },
    "nav_dashboard": {"fa": "Dashboard", "en": "Dashboard", "ar": "لوحة القيادة"},
    "nav_cost": {"fa": "Cost & Margin", "en": "Cost & Margin", "ar": "التكلفة والهامش"},
    "nav_distribution": {"fa": "Distribution", "en": "Distribution", "ar": "الأداء اللوجستي"},
    "nav_alerts": {"fa": "Alerts", "en": "Alerts", "ar": "التنبيهات"},
    "nav_optimize": {"fa": "Optimization", "en": "Optimization", "ar": "التحسين"},
    "nav_orders": {"fa": "Orders", "en": "Orders", "ar": "الطلبات"},
    "nav_logistics": {"fa": "Logistics", "en": "Logistics", "ar": "اللوجستيات"},
    "logout": {"fa": "Sign out", "en": "Sign out", "ar": "خروج"},
    "employee_code": {"fa": "Employee code", "en": "Employee code", "ar": "رمز الموظف"},
    "password": {"fa": "Password", "en": "Password", "ar": "كلمة المرور"},
    "otp_code": {"fa": "OTP code", "en": "OTP code", "ar": "رمز لمرة واحدة"},
    "create_order": {"fa": "Create order", "en": "Create order", "ar": "إنشاء طلب"},
    "create_shipment": {"fa": "Create shipment", "en": "Create shipment", "ar": "إنشاء شحنة"},
    "track_shipment": {"fa": "Track", "en": "Track", "ar": "تتبع"},
    "inventory": {"fa": "Inventory", "en": "Inventory", "ar": "المخزون"},
    "filter_subsidiary": {"fa": "Subsidiary", "en": "Subsidiary", "ar": "الشركة التابعة"},
    "filter_product": {"fa": "Product", "en": "Product", "ar": "المنتج"},
    "filter_region": {"fa": "Region", "en": "Region", "ar": "المنطقة"},
    "filter_period": {"fa": "Period", "en": "Period", "ar": "الفترة"},
    "kpi_otif": {"fa": "On-Time In-Full (OTIF)", "en": "On-Time In-Full", "ar": "التسليم في الوقت"},
    "kpi_fill": {"fa": "Warehouse fill", "en": "Warehouse Fill", "ar": "امتلاء المستودع"},
    "kpi_margin": {"fa": "Operating margin", "en": "Operating Margin", "ar": "هامش التشغيل"},
    "kpi_orders": {"fa": "Orders today", "en": "Orders Today", "ar": "طلبات اليوم"},
    "kpi_ships": {"fa": "Ships in port", "en": "Ships in Port", "ar": "السفن في الميناء"},
    "kpi_eta": {"fa": "Average ETA (days)", "en": "Avg ETA (days)", "ar": "متوسط الوصول"},
    "cost_per_ton": {"fa": "Cost per ton", "en": "Cost per Ton", "ar": "التكلفة للطن"},
    "margin_per_unit": {"fa": "Unit profit margin", "en": "Unit Margin", "ar": "هامش الوحدة"},
    "alerts_title": {"fa": "Smart alerts", "en": "Smart Alerts", "ar": "تنبيهات ذكية"},
    "run_budget_check": {"fa": "Budget deviation check", "en": "Run Budget Check", "ar": "فحص انحراف الميزانية"},
    "acknowledge": {"fa": "Acknowledge", "en": "Acknowledge", "ar": "إقرار"},
    "login": {"fa": "Sign in", "en": "Sign in", "ar": "تسجيل الدخول"},
    "role_executive": {"fa": "Senior manager", "en": "Executive", "ar": "تنفيذي"},
    "role_analyst": {"fa": "Analyst", "en": "Analyst", "ar": "محلل"},
    "role_logistics": {"fa": "Logistics", "en": "Logistics", "ar": "اللوجستيات"},
    "role_sales": {"fa": "Sales", "en": "Sales", "ar": "المبيعات"},
    "no_alerts": {"fa": "No active alerts", "en": "No active alerts", "ar": "لا توجد تنبيهات"},
    "period_7d": {"fa": "7 days", "en": "7 days", "ar": "٧ أيام"},
    "period_30d": {"fa": "30 days", "en": "30 days", "ar": "٣٠ يوماً"},
    "period_90d": {"fa": "90 days", "en": "90 days", "ar": "٩٠ يوماً"},
    "all": {"fa": "All", "en": "All", "ar": "الكل"},
}


def t(key: str, locale: str = "fa") -> str:
    entry = MESSAGES.get(key, {})
    return entry.get(locale) or entry.get("en") or key


def bundle(locale: str = "fa") -> dict[str, str]:
    return {k: t(k, locale) for k in MESSAGES}
