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



📄 مستند SRS – محصول ۳: تحول دیجیتال و یکپارچه‌سازی زنجیره ارزش (با قابلیت ثبت اختراع)
۱. مقدمه
هدف: پیاده‌سازی یک پلتفرم یکپارچه مبتنی بر معماری Data Mesh که زنجیره تأمین، تولید، توزیع و فروش محصولات پتروشیمی را به‌صورت لحظه‌ای به هم متصل کرده و با استفاده از هوش مصنوعی، تصمیم‌گیری‌های استراتژیک و عملیاتی را بهینه‌سازی کند .

نوآوری ثبت اختراع: برخلاف اختراع Honeywell که بر پلتفرم متمرکز وب‌بیس تأکید دارد، این سیستم از معماری Data Mesh با مالکیت غیرمتمرکز داده استفاده می‌کند و حلقه‌های تأمین، تولید، توزیع و فروش را در یک مدل بهینه‌سازی یکپارچه ترکیب می‌کند .

۲. نیازمندی‌های عملکردی (با تأکید بر قابلیت‌های اختراع)
شناسه	نیاز	قابلیت ثبت اختراع
FR-DATA-01	یکپارچه‌سازی داده‌های تولید، انبارداری، حمل‌ونقل و فروش با معماری Data Mesh (مالکیت غیرمتمرکز داده)	معماری Data Mesh صنعتی (نوآوری اصلی)
FR-ML-01	پیش‌بینی هم‌زمان تقاضا، قیمت و تخصیص بهینه خوراک با رویکرد بیشینه‌سازی حاشیه سود کل هلدینگ	پیش‌بینی و بهینه‌سازی یکپارچه
FR-ML-02	بهینه‌سازی تخصیص خوراک بین واحدهای تولیدی با الگوریتم‌های برنامه‌ریزی خطی و LP	بهینه‌سازی تخصیص منابع
FR-LOG-01	ردیابی لحظه‌ای محموله‌ها با GPS و AIS و اتصال به سامانه‌های گمرکی و بنادر ایران	بومی‌سازی لجستیک ایران
FR-BI-01	تولید خودکار گزارش‌های "هزینه تمام‌شده هر تن محصول" و "حاشیه سود هر واحد تولیدی"	گزارش‌دهی یکپارچه سودآوری
🧪 کد تولید داده‌های سنتتیک (یکپارچه برای هر سه حوزه)
کد زیر داده‌های ۱۰,۰۰۰ رکورد (۱ رکورد در ثانیه) را برای هر سه حوزه به‌صورت یکپارچه تولید می‌کند تا بتوان از آن برای آموزش مدل‌های هر سه محصول استفاده کرد.

python
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random

# ==============================================
# پارامترهای تولید داده
# ==============================================
NUM_RECORDS = 10000
START_TIME = datetime(2026, 7, 22, 8, 0, 0)

# ==============================================
# تولید برچسب زمانی (1 رکورد در ثانیه)
# ==============================================
timestamps = [START_TIME + timedelta(seconds=i) for i in range(NUM_RECORDS)]
t = np.linspace(0, 10 * np.pi, NUM_RECORDS)  # برای الگوهای سیکلی

# ==============================================
# 1. متغیرهای حوزه بهینه‌سازی تولید
# ==============================================

# دمای راکتور - محدوده 150 تا 350 درجه سانتی‌گراد
reactor_temp = 250 + 30 * np.sin(t * 0.5) + 0.01 * np.arange(NUM_RECORDS) + np.random.normal(0, 2, NUM_RECORDS)
reactor_temp = np.clip(reactor_temp, 150, 350)

# فشار راکتور - محدوده 10 تا 40 بار
reactor_pressure = 25 + 5 * np.sin(t * 0.3) + 0.005 * np.arange(NUM_RECORDS) + np.random.normal(0, 0.8, NUM_RECORDS)
reactor_pressure = np.clip(reactor_pressure, 10, 40)

# دبی خوراک ورودی - محدوده 100 تا 500 مترمکعب بر ساعت
feed_flow = 300 + 80 * np.sin(t * 0.2 + 1.2) + np.random.normal(0, 5, NUM_RECORDS)
feed_flow = np.clip(feed_flow, 100, 500)

# کیفیت محصول (MFI - شاخص جریان مذاب) - محدوده 2 تا 10
mfi_quality = 5 + 2 * np.sin(t * 0.3 + 0.5) + 0.002 * np.arange(NUM_RECORDS) + np.random.normal(0, 0.3, NUM_RECORDS)
mfi_quality = np.clip(mfi_quality, 2, 10)

# ==============================================
# 2. متغیرهای حوزه مدیریت انرژی و کربن
# ==============================================

# مصرف برق (توان لحظه‌ای) - محدوده 5 تا 25 مگاوات
electricity_power = 15 + 5 * np.sin(t * 0.2) + 0.005 * np.arange(NUM_RECORDS) + np.random.normal(0, 0.5, NUM_RECORDS)
electricity_power = np.clip(electricity_power, 5, 25)

# مصرف سوخت گاز طبیعی - محدوده 50 تا 150 هزار مترمکعب بر ساعت
fuel_gas_flow = 100 + 30 * np.sin(t * 0.15 + 1.5) + np.random.normal(0, 3, NUM_RECORDS)
fuel_gas_flow = np.clip(fuel_gas_flow, 50, 150)

# مصرف بخار - محدوده 10 تا 50 تن بر ساعت
steam_flow = 30 + 10 * np.sin(t * 0.25 + 0.8) + np.random.normal(0, 1.5, NUM_RECORDS)
steam_flow = np.clip(steam_flow, 10, 50)

# انتشار کربن Scope 1 - کیلوگرم CO2 به ازای هر تن محصول
carbon_scope1 = 0.2 * fuel_gas_flow + 0.3 * steam_flow + np.random.normal(0, 2, NUM_RECORDS)
carbon_scope1 = np.clip(carbon_scope1, 20, 80)

# انتشار کربن Scope 2 (برق خریداری‌شده)
carbon_scope2 = 0.15 * electricity_power + np.random.normal(0, 1, NUM_RECORDS)
carbon_scope2 = np.clip(carbon_scope2, 5, 30)

# انتشار کربن Scope 3 (زنجیره تأمین و توزیع) - شبیه‌سازی
carbon_scope3 = 0.1 * feed_flow + 0.05 * np.random.randn(NUM_RECORDS) + 10
carbon_scope3 = np.clip(carbon_scope3, 5, 25)

# انتشار کربن کل
carbon_total = carbon_scope1 + carbon_scope2 + carbon_scope3

# ==============================================
# 3. متغیرهای حوزه تحول دیجیتال و زنجیره ارزش
# ==============================================

# قیمت نفت خام - محدوده 60 تا 90 دلار بر بشکه
oil_price = 75 + 5 * np.sin(t * 0.15) + 2 * np.random.randn(NUM_RECORDS)
oil_price = np.clip(oil_price, 60, 90)

# قیمت محصول (HDPE) - وابسته به قیمت نفت
price_hdpe = 900 + 0.5 * (oil_price - 75) * 10 + 20 * np.sin(t * 0.2) + 5 * np.random.randn(NUM_RECORDS)
price_hdpe = np.clip(price_hdpe, 750, 1100)

# تعداد سفارشات دریافتی (توزیع پواسون)
orders_received = np.random.poisson(lam=2, size=NUM_RECORDS)

# موجودی انبار - محدوده 2000 تا 8000 تن
inventory = 5000 + 1000 * np.sin(t * 0.2) + np.random.normal(0, 100, NUM_RECORDS)
inventory = np.clip(inventory, 2000, 8000)

# زمان تحویل (ETA) - محدوده 2 تا 15 روز
eta_days = 7 + 3 * np.sin(t * 0.15) + 2 * np.random.randn(NUM_RECORDS)
eta_days = np.clip(np.round(eta_days, 1), 2, 15)

# ==============================================
# 4. متغیرهای هدف (خروجی‌های اصلی)
# ==============================================

# راندمان تولید (Efficiency) - تابعی از دما و فشار
production_efficiency = ((reactor_temp - 200) / 150 * 20 + (reactor_pressure - 20) / 20 * 10 + 60 
                         + np.random.normal(0, 2, NUM_RECORDS))
production_efficiency = np.clip(production_efficiency, 40, 98)

# شدت انرژی (SEC) - محدوده 500 تا 800 کیلوگرم معادل نفت خام بر تن
energy_intensity = (600 + 0.5 * fuel_gas_flow + 2 * steam_flow - 0.1 * feed_flow 
                    + 0.3 * reactor_temp + np.random.normal(0, 10, NUM_RECORDS))
energy_intensity = np.clip(energy_intensity, 500, 800)

# حاشیه سود عملیاتی - درصد
operating_margin = 20 + 3 * np.sin(t * 0.2 + 1.0) + 2 * np.random.randn(NUM_RECORDS)
operating_margin = np.clip(operating_margin, 10, 35)

# ==============================================
# ساخت دیتافریم یکپارچه
# ==============================================
df = pd.DataFrame({
    'timestamp': timestamps,
    
    # حوزه ۱: بهینه‌سازی تولید
    'reactor_temp_c': np.round(reactor_temp, 2),
    'reactor_pressure_bar': np.round(reactor_pressure, 2),
    'feed_flow_m3h': np.round(feed_flow, 2),
    'mfi_quality': np.round(mfi_quality, 2),
    'production_efficiency_percent': np.round(production_efficiency, 2),
    
    # حوزه ۲: مدیریت انرژی و کربن
    'electricity_power_mw': np.round(electricity_power, 2),
    'fuel_gas_flow_km3h': np.round(fuel_gas_flow, 2),
    'steam_flow_tonh': np.round(steam_flow, 2),
    'carbon_scope1_kgco2_ton': np.round(carbon_scope1, 2),
    'carbon_scope2_kgco2_ton': np.round(carbon_scope2, 2),
    'carbon_scope3_kgco2_ton': np.round(carbon_scope3, 2),
    'carbon_total_kgco2_ton': np.round(carbon_total, 2),
    'energy_intensity_kgoe_ton': np.round(energy_intensity, 2),
    
    # حوزه ۳: تحول دیجیتال و زنجیره ارزش
    'oil_price_usd_bbl': np.round(oil_price, 2),
    'price_hdpe_usd_ton': np.round(price_hdpe, 2),
    'orders_received': orders_received,
    'inventory_tons': np.round(inventory, 2),
    'eta_days': eta_days,
    'operating_margin_percent': np.round(operating_margin, 2)
})

# ==============================================
# ذخیره فایل
# ==============================================
output_file = "integrated_petrochemical_data_10k.csv"
df.to_csv(output_file, index=False)
print(f"✅ داده‌های یکپارچه در فایل '{output_file}' ذخیره شد.")
print(f"📊 تعداد رکوردها: {len(df):,} - تعداد متغیرها: {len(df.columns)}")

print("\n🔍 نمونه داده‌های تولید شده:")
print(df.head())

print("\n📈 آمار توصیفی داده‌ها:")
print(df.describe())
🧩 جمع‌بندی: قابلیت‌های کلیدی ثبت اختراع
حوزه	قابلیت‌های نوآورانه برای ثبت اختراع
بهینه‌سازی تولید	1. حسگرهای مجازی هوشمند برای پیش‌بینی بلادرنگ خواص محصول 
2. بهینه‌سازی سه‌هدفه (هزینه، کیفیت، انرژی) با PSO
3. تولید داده‌های مصنوعی با GAN برای آموزش در شرایط کم‌داده
مدیریت انرژی و کربن	1. محاسبه کامل Scope 1، 2 و 3 (برخلاف اختراعات موجود)
2. شبیه‌سازی سناریوهای کربن‌محور (چه-اگر)
3. بومی‌سازی برای قوانین و ضرایب انتشار ایران
تحول دیجیتال	1. معماری Data Mesh صنعتی با مالکیت غیرمتمرکز داده
2. پیش‌بینی و بهینه‌سازی یکپارچه کل زنجیره ارزش 
3. اتصال به سامانه‌های گمرکی و بنادر ایران

