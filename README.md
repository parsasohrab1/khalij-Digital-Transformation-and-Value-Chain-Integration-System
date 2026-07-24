# khalij-Digital-Transformation-and-Value-Chain-Integration-System

۱. مقدمه (Introduction)
هدف: پیاده‌سازی یک پلتفرم یکپارچه مبتنی بر داده که زنجیره تأمین، تولید، توزیع و فروش محصولات پتروشیمی را به‌صورت لحظه‌ای به هم متصل کرده و با استفاده از هوش مصنوعی، تصمیم‌گیری‌های استراتژیک و عملیاتی را بهینه‌سازی کند. این سیستم، دیدگاه "از میدان تا بازار" (Well-to-Market) را محقق می‌سازد.

چالش‌های موجود: ناهماهنگی بین واحدهای تولیدی و بازاریابی، عدم شفافیت در موجودی انبارها و هزینه‌های بالای لجستیک.

دامنه: شامل کلیه شرکت‌های تابعه هلدینگ خلیج‌فارس و ارتباط با تأمین‌کنندگان خارجی و مشتریان داخلی/خارجی.

۲. نیازمندی‌های کلی (General Requirements)
شناسه	نیاز	اولویت
R-GEN-01	یکپارچه‌سازی داده‌های تولید، انبارداری، حمل‌ونقل و فروش در یک "دریاچه داده" (Data Lake) متمرکز	بالا
R-GEN-02	ارائه پنل مدیریتی یکپارچه (Command Center) برای پایش کل زنجیره ارزش	بالا
R-GEN-03	ارتباط با سیستم‌های ERP و SAP موجود در شرکت‌های تابعه از طریق APIهای استاندارد	بالا
R-GEN-04	پشتیبانی از چندزبانگی (فارسی، انگلیسی، عربی) برای کاربران بین‌المللی	متوسط
۳. نیازمندی‌های عملکردی (Functional Requirements)
۳-۱. ماژول یکپارچه‌سازی داده (Data Integration Hub)
FR-DATA-01: سیستم باید قابلیت اتصال به تمام پایگاه‌های داده عملیاتی (OLTP) شرکت‌های تابعه را داشته باشد (Oracle، SQL Server، PostgreSQL).

FR-DATA-02: پیاده‌سازی الگوی Data Mesh برای غیرمتمرکزسازی مالکیت داده‌ها و تسهیل دسترسی هر واحد به داده‌های موردنیاز خود.

FR-DATA-03: تطبیق و استانداردسازی واحدهای اندازه‌گیری و شناسه‌های کالا (مانند کد HS و کد محصولات داخلی) در کل هلدینگ.

۳-۲. ماژول تحلیل و پیش‌بینی زنجیره تأمین (Supply Chain Analytics)
FR-ML-01: پیش‌بینی تقاضای محصولات (به‌تفکیک گریدهای مختلف پلیمر) برای ۳ ماه آینده با استفاده از مدل‌های Prophet یا LSTM بر اساس داده‌های تاریخی فروش و شاخص‌های اقتصاد کلان (قیمت نفت، نرخ ارز).

FR-ML-02: بهینه‌سازی تخصیص خوراک (مواد اولیه) بین واحدهای تولیدی مختلف به‌گونه‌ای که حاشیه سود کل هلدینگ بیشینه شود (با استفاده از الگوریتم‌های برنامه‌ریزی خطی).

FR-ML-03: پیش‌بینی نوسانات قیمت مواد اولیه و محصولات نهایی برای بهینه‌سازی زمان خرید و فروش (Trading Optimization).

۳-۳. ماژول ردیابی و شفافیت لجستیک (Logistics & Traceability)
FR-LOG-01: ردیابی لحظه‌ای محموله‌ها (دریایی، زمینی و ریلی) با استفاده از GPS و سیستم‌های AIS.

FR-LOG-02: محاسبه خودکار زمان تخمینی رسیدن (ETA) محموله‌ها با در نظر گرفتن شرایط آب‌وهوایی و ترافیک بنادر.

FR-LOG-03: ارائه داشبورد به مشتریان برای مشاهده وضعیت سفارش‌های خود و زمان تحویل.

۳-۴. ماژول مدیریت یکپارچه سفارشات و فروش (Order-to-Cash)
FR-ORDER-01: ثبت و مدیریت یکپارچه سفارشات از تمام کانال‌های فروش (آنلاین، قراردادی، مزایده).

FR-ORDER-02: تخصیص هوشمند سفارشات به انبارها یا واحدهای تولیدی بر اساس نزدیکی جغرافیایی، موجودی و هزینه حمل.

FR-ORDER-03: اتصال به سیستم‌های مالی برای صدور خودکار فاکتور و پیگیری دریافت وجه.

۳-۵. ماژول گزارش‌دهی و هوش تجاری (BI & Reporting)
FR-BI-01: تولید خودکار گزارش‌های کلیدی نظیر "هزینه تمام‌شده هر تن محصول"، "حاشیه سود هر واحد تولیدی" و "عملکرد توزیع".

FR-BI-02: داشبوردهای تعاملی با قابلیت فیلتر بر اساس شرکت تابعه، محصول، منطقه جغرافیایی و بازه زمانی.

FR-BI-03: ایجاد هشدارهای هوشمند برای انحراف از برنامه تولید، فروش یا بودجه تعیین‌شده.

۴. نیازمندی‌های غیرعملکردی (Non-Functional Requirements)
شناسه	نیاز	مقدار هدف
NFR-PER-01	زمان پاسخ‌دهی پلتفرم برای نمایش داشبوردها	کمتر از ۲ ثانیه
NFR-PER-02	زمان پردازش پیش‌بینی تقاضا (برای ۳ ماه)	کمتر از ۵ دقیقه
NFR-AVAIL-01	در دسترس بودن سیستم	۹۹.۹۵٪ (کمتر از ۲۲ دقیقه توقف در ماه)
NFR-SEC-01	رمزنگاری داده‌های حساس (قیمت‌ها و قراردادها) در حالت ذخیره‌سازی (AES-256) و انتقال (TLS 1.3)	اجباری
NFR-SEC-02	پیاده‌سازی دقیق نقش‌های دسترسی (RBAC) با تفکیک سطوح مدیریتی و عملیاتی	اجباری
NFR-SCL-01	قابلیت مقیاس‌پذیری افقی برای مدیریت داده‌های ۵۰,۰۰۰ تراکنش در ثانیه	مورد انتظار
۵. معماری فنی (Technical Architecture)
معماری کلی: میکروسرویس‌ها (Microservices) با رویکرد Data Mesh

زبان برنامه‌نویسی: Python (برای سرویس‌های ML)، Java (برای سرویس‌های سنگین تراکنشی)

چارچوب وب: FastAPI و Spring Boot

پایگاه داده:

داده‌های تراکنشی: PostgreSQL (با شاردینگ)

داده‌های سری زمانی: TimescaleDB

داده‌های تحلیلی: Apache Druid

ارسال پیام (Message Broker): Apache Kafka (با topicهای مجزا برای هر شرکت تابعه)

پردازش جریانی: Apache Flink برای پردازش داده‌های لحظه‌ای سنسورها و GPS

Data Catalog: Apache Atlas برای مدیریت متادیتا و نسب‌شناسی داده (Data Lineage)

MLOps: MLflow + Kubeflow

🧪 کد تولید داده‌های سنتتیک (Synthetic Data Generator)
کد زیر داده‌های ۱۰,۰۰۰ رکورد (حدود ۲.۷ ساعت عملیات) را برای متغیرهای کلیدی زنجیره ارزش شبیه‌سازی می‌کند. این داده‌ها شامل اطلاعات سفارشات، موجودی، قیمت‌ها و وضعیت حمل‌ونقل هستند که با نرخ ۱ رکورد در ثانیه تولید می‌شوند.

python
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random

# ==============================================
# پارامترهای تولید داده
# ==============================================
NUM_RECORDS = 10000          # 10,000 رکورد (ثانیه)
START_TIME = datetime(2026, 7, 22, 8, 0, 0)   # زمان شروع

# ==============================================
# تولید برچسب زمانی با فاصله 1 ثانیه
# ==============================================
timestamps = [START_TIME + timedelta(seconds=i) for i in range(NUM_RECORDS)]

# ==============================================
# تولید داده‌های مصنوعی برای زنجیره ارزش
# ==============================================

# ------------------------
# 1. داده‌های سفارشات (Orders)
# ------------------------
# شبیه‌سازی تعداد سفارشات دریافتی در هر ثانیه (توزیع پواسون)
orders_received = np.random.poisson(lam=2, size=NUM_RECORDS)  # میانگین ۲ سفارش در ثانیه

# ارزش هر سفارش (دلار) - محدوده ۱۰,۰۰۰ تا ۲۵۰,۰۰۰ دلار
order_value = np.random.uniform(10000, 250000, size=NUM_RECORDS)

# نوع محصول (گریدهای مختلف پلیمر)
product_types = np.random.choice(['HDPE', 'LDPE', 'LLDPE', 'PP', 'PET'], size=NUM_RECORDS, p=[0.3, 0.2, 0.2, 0.2, 0.1])

# میزان سفارش (تن) - محدوده ۲۰ تا ۵۰۰ تن
order_quantity_tons = np.random.uniform(20, 500, size=NUM_RECORDS)

# ------------------------
# 2. داده‌های موجودی انبار (Inventory)
# ------------------------
# موجودی انبارهای مختلف (در تن)
inventory_bandar_abbas = 5000 + 1000 * np.sin(np.linspace(0, 4*np.pi, NUM_RECORDS)) + np.random.normal(0, 100, NUM_RECORDS)
inventory_bandar_abbas = np.clip(inventory_bandar_abbas, 2000, 8000)

inventory_tehran = 3000 + 800 * np.sin(np.linspace(0, 4*np.pi, NUM_RECORDS) + 1.5) + np.random.normal(0, 80, NUM_RECORDS)
inventory_tehran = np.clip(inventory_tehran, 1000, 6000)

inventory_assaluyeh = 8000 + 1500 * np.sin(np.linspace(0, 4*np.pi, NUM_RECORDS) + 3.0) + np.random.normal(0, 150, NUM_RECORDS)
inventory_assaluyeh = np.clip(inventory_assaluyeh, 4000, 12000)

# موجودی کل
total_inventory = inventory_bandar_abbas + inventory_tehran + inventory_assaluyeh

# ------------------------
# 3. داده‌های قیمت (Pricing)
# ------------------------
# قیمت نفت خام (دلار بر بشکه) - شبیه‌سازی نوسانات روزانه
oil_price = 75 + 5 * np.sin(np.linspace(0, 3*np.pi, NUM_RECORDS)) + 2 * np.random.randn(NUM_RECORDS)
oil_price = np.clip(oil_price, 60, 90)

# قیمت محصولات (دلار بر تن) - وابسته به قیمت نفت و تقاضا
price_hdpe = 900 + 0.5 * (oil_price - 75) * 10 + 20 * np.sin(np.linspace(0, 2*np.pi, NUM_RECORDS)) + 5 * np.random.randn(NUM_RECORDS)
price_hdpe = np.clip(price_hdpe, 750, 1100)

price_pp = 850 + 0.4 * (oil_price - 75) * 10 + 25 * np.sin(np.linspace(0, 2*np.pi, NUM_RECORDS) + 1.0) + 5 * np.random.randn(NUM_RECORDS)
price_pp = np.clip(price_pp, 700, 1050)

# قیمت خوراک (اتیلن) - محدوده ۷۰۰ تا ۱۰۰۰ دلار بر تن
feedstock_price = 800 + 0.3 * (oil_price - 75) * 10 + 15 * np.sin(np.linspace(0, 2*np.pi, NUM_RECORDS) + 2.0) + 5 * np.random.randn(NUM_RECORDS)
feedstock_price = np.clip(feedstock_price, 700, 1000)

# ------------------------
# 4. داده‌های لجستیک و حمل‌ونقل (Logistics)
# ------------------------
# تعداد کشتی‌های در حال بارگیری در بنادر
ships_in_port = np.random.choice([0, 1, 2, 3, 4], size=NUM_RECORDS, p=[0.1, 0.25, 0.35, 0.2, 0.1])

# زمان تخمینی تحویل (ETA) به مشتری - محدوده ۲ تا ۱۵ روز
eta_days = 7 + 3 * np.sin(np.linspace(0, 2*np.pi, NUM_RECORDS)) + 2 * np.random.randn(NUM_RECORDS)
eta_days = np.clip(np.round(eta_days, 1), 2, 15)

# هزینه حمل هر تن (دلار) - تابعی از فاصله و قیمت سوخت
logistics_cost_per_ton = 50 + 0.2 * (oil_price - 75) + 10 * np.random.randn(NUM_RECORDS)
logistics_cost_per_ton = np.clip(logistics_cost_per_ton, 30, 80)

# ------------------------
# 5. شاخص‌های کلیدی عملکرد (KPIs)
# ------------------------
# شاخص پر شدن انبار (Warehouse Fill Rate) - درصد
warehouse_fill_rate = 70 + 10 * np.sin(np.linspace(0, 2*np.pi, NUM_RECORDS)) + 5 * np.random.randn(NUM_RECORDS)
warehouse_fill_rate = np.clip(warehouse_fill_rate, 40, 95)

# شاخص نرخ تحویل به‌موقع (OTIF - On-Time In-Full) - درصد
otif_rate = 88 + 5 * np.sin(np.linspace(0, 2*np.pi, NUM_RECORDS) + 0.5) + 3 * np.random.randn(NUM_RECORDS)
otif_rate = np.clip(otif_rate, 70, 99)

# حاشیه سود عملیاتی (درصد)
operating_margin = 20 + 3 * np.sin(np.linspace(0, 2*np.pi, NUM_RECORDS) + 1.0) + 2 * np.random.randn(NUM_RECORDS)
operating_margin = np.clip(operating_margin, 10, 35)

# ==============================================
# ساخت دیتافریم نهایی
# ==============================================
df = pd.DataFrame({
    'timestamp': timestamps,
    
    # داده‌های سفارشات
    'orders_received': orders_received,
    'order_value_usd': np.round(order_value, 2),
    'product_type': product_types,
    'order_quantity_tons': np.round(order_quantity_tons, 2),
    
    # داده‌های موجودی
    'inventory_bandar_abbas_tons': np.round(inventory_bandar_abbas, 2),
    'inventory_tehran_tons': np.round(inventory_tehran, 2),
    'inventory_assaluyeh_tons': np.round(inventory_assaluyeh, 2),
    'total_inventory_tons': np.round(total_inventory, 2),
    
    # داده‌های قیمت
    'oil_price_usd_bbl': np.round(oil_price, 2),
    'price_hdpe_usd_ton': np.round(price_hdpe, 2),
    'price_pp_usd_ton': np.round(price_pp, 2),
    'feedstock_price_usd_ton': np.round(feedstock_price, 2),
    
    # داده‌های لجستیک
    'ships_in_port': ships_in_port,
    'eta_days': eta_days,
    'logistics_cost_per_ton_usd': np.round(logistics_cost_per_ton, 2),
    
    # شاخص‌های عملکرد
    'warehouse_fill_rate_percent': np.round(warehouse_fill_rate, 2),
    'otif_rate_percent': np.round(otif_rate, 2),
    'operating_margin_percent': np.round(operating_margin, 2)
})

# ==============================================
# ذخیره در فایل CSV
# ==============================================
output_file = "digital_value_chain_data_10k.csv"
df.to_csv(output_file, index=False)
print(f"✅ داده‌های زنجیره ارزش با موفقیت در فایل '{output_file}' ذخیره شدند.")
print(f"📊 تعداد رکوردها: {len(df):,} - تعداد متغیرها: {len(df.columns)}")

print("\n🔍 نمونه داده‌های تولید شده:")
print(df.head())

print("\n📈 آمار توصیفی داده‌ها:")
print(df.describe(include='all'))

# نمایش توزیع محصولات
print("\n📊 توزیع انواع محصولات:")
print(df['product_type'].value_counts())
📊 خروجی نمونه (نمایش ۵ رکورد اول):
timestamp	orders_received	order_value_usd	product_type	order_quantity_tons	inventory_bandar_abbas_tons	...	oil_price_usd_bbl	price_hdpe_usd_ton	ships_in_port	eta_days	otif_rate_percent	operating_margin_percent
2026-07-22 08:00:00	2	152340.75	HDPE	245.30	5120.45	...	76.50	935.20	2	7.5	89.50	21.30
2026-07-22 08:00:01	1	98750.20	PP	180.50	5080.12	...	76.80	938.50	1	6.8	90.10	22.10
...	...	...	...	...	...	...	...	...	...	...	...	...
🔧 نکات فنی پیاده‌سازی کد:
نرخ نمونه‌برداری: timedelta(seconds=i) تضمین می‌کند که داده‌ها با نرخ ۱ رکورد در ثانیه شبیه‌سازی شوند.

تنوع داده‌ها: شامل ترکیبی از داده‌های عددی پیوسته (قیمت‌ها)، عددی گسسته (تعداد سفارشات، کشتی‌ها) و داده‌های کیفی (نوع محصول) است.

روابط اقتصادی: قیمت محصولات و خوراک به‌صورت وابسته به قیمت نفت شبیه‌سازی شده‌اند که بازتاب دنیای واقعی است.

شاخص‌های عملکرد: شاخص‌های کلیدی مانند OTIF و حاشیه سود به‌عنوان معیارهای ارزیابی عملکرد زنجیره ارزش در نظر گرفته شده‌اند.

کاربرد در دنیای واقعی: این داده‌ها می‌توانند برای پیاده‌سازی مدل‌های پیش‌بینی تقاضا، بهینه‌سازی تخصیص موجودی، و تحلیل حاشیه سود در پلتفرم تحول دیجیتال استفاده شوند.

💡 پیشنهاد برای گام بعدی:
پس از تولید این داده‌ها، می‌توانید:

پیاده‌سازی یک مدل پیش‌بینی تقاضا با استفاده از Prophet یا LSTM روی داده‌های تاریخی سفارشات.

طراحی یک داشبورد هوش تجاری (BI) با PowerBI یا Tableau برای نمایش لحظه‌ای شاخص‌های کلیدی.

پیاده‌سازی یک سیستم توصیه‌گر برای تخصیص بهینه سفارشات به انبارها بر اساس کمترین هزینه حمل و نزدیکترین موجودی
