# khalij-Digital-Transformation-and-Value-Chain-Integration-System

## Quick start (Demo MVP)

```bash
# 1) Environment
cp .env.example .env

# 2) Seed CSV (auto-generates if missing)
python scripts/ensure_seed_data.py

# 3) Stack
docker compose up --build -d

# 4) Open Command Center
# UI:  http://localhost:8010
# API: http://localhost:8000/docs
```

**Demo login**
- Employee: `demo-admin`
- Password: `ChangeMe123!`
- OTP: TOTP with secret `3MYXLVCKBIRJUTD6` (Google Authenticator / `pyotp`)

```bash
python -c "import pyotp; print(pyotp.TOTP('3MYXLVCKBIRJUTD6').now())"
```

**Offline / local PoC (no Docker)**
```bash
python scripts/ensure_seed_data.py
python scripts/demo_patent_poc.py
python scripts/security_scan.py
python -m pytest tests/test_smoke.py -q
```

**Production-like TLS + HA**
```bash
python scripts/generate_tls_certs.py
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
# https://localhost  (nginx → Command Center + /api → gateway pool)
```

| Service | Port |
|---------|------|
| API Gateway | 8000 |
| Data Integration | 8001 |
| Supply Chain Analytics | 8002 |
| Logistics | 8003 |
| Order-to-Cash | 8004 |
| BI Reporting | 8005 |
| Command Center UI | 8010 |
| Customer Portal | 8011 |

**Customer portal (no internal login)**  
http://localhost:8011 — enter `ORD-…` to view order + shipment status via Gateway.

**Persist / scale proofs**
```bash
# Existing Postgres volume: apply schema upgrades
# psql $POSTGRES_DSN -f scripts/migrate_persist.sql

python scripts/prove_tps.py --iterations 20000 --workers 32
# optional network: python scripts/prove_tps.py --url http://127.0.0.1:8000/bench/ping
```

Reports: `docs/TPS_PROOF.md`, `reports/tps_proof.json`

1. Introduction
Purpose: Implement an integrated data-driven platform that connects the supply chain, production, distribution and sales of petrochemical products in real time and, using artificial intelligence, optimizes strategic and operational decision-making. This system realizes the "Well-to-Market" perspective.

Existing challenges: Lack of coordination between production and marketing units, lack of transparency in warehouse inventory, and high logistics costs.

Scope: Includes all subsidiaries of the Persian Gulf Holding and the connection with foreign suppliers and domestic/foreign customers.

2. General Requirements
ID	Requirement	Priority
R-GEN-01	Integrate production, warehousing, transportation and sales data into a centralized "Data Lake"	High
R-GEN-02	Provide an integrated management panel (Command Center) for monitoring the entire value chain	High
R-GEN-03	Connect to the existing ERP and SAP systems of subsidiaries through standard APIs	High
R-GEN-04	Multilingual support (Persian, English, Arabic) for international users	Medium
3. Functional Requirements
3-1. Data Integration Module (Data Integration Hub)
FR-DATA-01: The system must be able to connect to all operational databases (OLTP) of subsidiaries (Oracle, SQL Server, PostgreSQL).

FR-DATA-02: Implement the Data Mesh pattern to decentralize data ownership and ease each unit's access to the data it needs.

FR-DATA-03: Matching and standardizing units of measurement and product identifiers (such as HS code and internal product codes) across the holding.

3-2. Supply Chain Analytics Module
FR-ML-01: Forecast product demand (by different polymer grades) for the next 3 months using Prophet or LSTM models based on historical sales data and macroeconomic indicators (oil price, exchange rate).

FR-ML-02: Optimize the allocation of feed (raw materials) among different production units so that the total profit margin of the holding is maximized (using linear programming algorithms).

FR-ML-03: Forecast price fluctuations of raw materials and final products to optimize buying and selling timing (Trading Optimization).

3-3. Logistics & Traceability Module
FR-LOG-01: Real-time tracking of shipments (sea, land and rail) using GPS and AIS systems.

FR-LOG-02: Automatic calculation of the estimated time of arrival (ETA) of shipments considering weather conditions and port traffic.

FR-LOG-03: Provide a dashboard to customers to view the status of their orders and delivery time.

3-4. Integrated Order and Sales Management Module (Order-to-Cash)
FR-ORDER-01: Integrated registration and management of orders from all sales channels (online, contractual, auction).

FR-ORDER-02: Intelligent allocation of orders to warehouses or production units based on geographic proximity, inventory and shipping cost.

FR-ORDER-03: Connection to financial systems for automatic invoice issuance and payment follow-up.

3-5. Reporting and Business Intelligence Module (BI & Reporting)
FR-BI-01: Automatic generation of key reports such as "cost per ton of product", "profit margin of each production unit" and "distribution performance".

FR-BI-02: Interactive dashboards with filtering by subsidiary, product, geographic region and time interval.

FR-BI-03: Creating smart alerts for deviations from the production, sales or budget plan.

4. Non-Functional Requirements
ID	Requirement	Target value
NFR-PER-01	Platform response time for displaying dashboards	Less than 2 seconds
NFR-PER-02	Demand forecast processing time (for 3 months)	Less than 5 minutes
NFR-AVAIL-01	System availability	99.95% (less than 22 minutes downtime per month)
NFR-SEC-01	Encryption of sensitive data (prices and contracts) at rest (AES-256) and in transit (TLS 1.3)	Mandatory
NFR-SEC-02	Precise implementation of access roles (RBAC) separating management and operational levels	Mandatory
NFR-SCL-01	Horizontal scalability to manage 50,000 transactions per second	Expected
5. Technical Architecture
Overall architecture: Microservices with a Data Mesh approach

Programming language: Python (for ML services), Java (for heavy transactional services)

Web framework: FastAPI and Spring Boot

Database:

Transactional data: PostgreSQL (with sharding)

Time-series data: TimescaleDB

Analytical data: Apache Druid

Message Broker: Apache Kafka (with separate topics for each subsidiary)

Stream processing: Apache Flink for real-time processing of sensor and GPS data

Data Catalog: Apache Atlas for metadata management and data lineage

MLOps: MLflow + Kubeflow

🧪 Synthetic Data Generator Code
The code below simulates 10,000 records (about 2.7 hours of operation) of data for the key variables of the value chain. These data include order, inventory, price and transportation status information, generated at a rate of 1 record per second.

python
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random

# ==============================================
# Data generation parameters
# ==============================================
NUM_RECORDS = 10000          # 10,000 records (seconds)
START_TIME = datetime(2026, 7, 22, 8, 0, 0)   # start time

# ==============================================
# Generate timestamps at 1-second intervals
# ==============================================
timestamps = [START_TIME + timedelta(seconds=i) for i in range(NUM_RECORDS)]

# ==============================================
# Generate synthetic data for the value chain
# ==============================================

# ------------------------
# 1. Orders data
# ------------------------
# Simulate the number of orders received per second (Poisson distribution)
orders_received = np.random.poisson(lam=2, size=NUM_RECORDS)  # average of 2 orders per second

# Value of each order (dollars) - range 10,000 to 250,000 dollars
order_value = np.random.uniform(10000, 250000, size=NUM_RECORDS)

# Product type (different polymer grades)
product_types = np.random.choice(['HDPE', 'LDPE', 'LLDPE', 'PP', 'PET'], size=NUM_RECORDS, p=[0.3, 0.2, 0.2, 0.2, 0.1])

# Order quantity (tons) - range 20 to 500 tons
order_quantity_tons = np.random.uniform(20, 500, size=NUM_RECORDS)

# ------------------------
# 2. Warehouse inventory data
# ------------------------
# Inventory of different warehouses (in tons)
inventory_bandar_abbas = 5000 + 1000 * np.sin(np.linspace(0, 4*np.pi, NUM_RECORDS)) + np.random.normal(0, 100, NUM_RECORDS)
inventory_bandar_abbas = np.clip(inventory_bandar_abbas, 2000, 8000)

inventory_tehran = 3000 + 800 * np.sin(np.linspace(0, 4*np.pi, NUM_RECORDS) + 1.5) + np.random.normal(0, 80, NUM_RECORDS)
inventory_tehran = np.clip(inventory_tehran, 1000, 6000)

inventory_assaluyeh = 8000 + 1500 * np.sin(np.linspace(0, 4*np.pi, NUM_RECORDS) + 3.0) + np.random.normal(0, 150, NUM_RECORDS)
inventory_assaluyeh = np.clip(inventory_assaluyeh, 4000, 12000)

# Total inventory
total_inventory = inventory_bandar_abbas + inventory_tehran + inventory_assaluyeh

# ------------------------
# 3. Pricing data
# ------------------------
# Crude oil price (dollars per barrel) - simulating daily fluctuations
oil_price = 75 + 5 * np.sin(np.linspace(0, 3*np.pi, NUM_RECORDS)) + 2 * np.random.randn(NUM_RECORDS)
oil_price = np.clip(oil_price, 60, 90)

# Product prices (dollars per ton) - dependent on oil price and demand
price_hdpe = 900 + 0.5 * (oil_price - 75) * 10 + 20 * np.sin(np.linspace(0, 2*np.pi, NUM_RECORDS)) + 5 * np.random.randn(NUM_RECORDS)
price_hdpe = np.clip(price_hdpe, 750, 1100)

price_pp = 850 + 0.4 * (oil_price - 75) * 10 + 25 * np.sin(np.linspace(0, 2*np.pi, NUM_RECORDS) + 1.0) + 5 * np.random.randn(NUM_RECORDS)
price_pp = np.clip(price_pp, 700, 1050)

# Feed price (ethylene) - range 700 to 1000 dollars per ton
feedstock_price = 800 + 0.3 * (oil_price - 75) * 10 + 15 * np.sin(np.linspace(0, 2*np.pi, NUM_RECORDS) + 2.0) + 5 * np.random.randn(NUM_RECORDS)
feedstock_price = np.clip(feedstock_price, 700, 1000)

# ------------------------
# 4. Logistics and transportation data
# ------------------------
# Number of ships loading at ports
ships_in_port = np.random.choice([0, 1, 2, 3, 4], size=NUM_RECORDS, p=[0.1, 0.25, 0.35, 0.2, 0.1])

# Estimated time of arrival (ETA) to the customer - range 2 to 15 days
eta_days = 7 + 3 * np.sin(np.linspace(0, 2*np.pi, NUM_RECORDS)) + 2 * np.random.randn(NUM_RECORDS)
eta_days = np.clip(np.round(eta_days, 1), 2, 15)

# Shipping cost per ton (dollars) - a function of distance and fuel price
logistics_cost_per_ton = 50 + 0.2 * (oil_price - 75) + 10 * np.random.randn(NUM_RECORDS)
logistics_cost_per_ton = np.clip(logistics_cost_per_ton, 30, 80)

# ------------------------
# 5. Key performance indicators (KPIs)
# ------------------------
# Warehouse Fill Rate - percent
warehouse_fill_rate = 70 + 10 * np.sin(np.linspace(0, 2*np.pi, NUM_RECORDS)) + 5 * np.random.randn(NUM_RECORDS)
warehouse_fill_rate = np.clip(warehouse_fill_rate, 40, 95)

# On-Time In-Full (OTIF) rate - percent
otif_rate = 88 + 5 * np.sin(np.linspace(0, 2*np.pi, NUM_RECORDS) + 0.5) + 3 * np.random.randn(NUM_RECORDS)
otif_rate = np.clip(otif_rate, 70, 99)

# Operating profit margin (percent)
operating_margin = 20 + 3 * np.sin(np.linspace(0, 2*np.pi, NUM_RECORDS) + 1.0) + 2 * np.random.randn(NUM_RECORDS)
operating_margin = np.clip(operating_margin, 10, 35)

# ==============================================
# Build the final dataframe
# ==============================================
df = pd.DataFrame({
    'timestamp': timestamps,
    
    # Orders data
    'orders_received': orders_received,
    'order_value_usd': np.round(order_value, 2),
    'product_type': product_types,
    'order_quantity_tons': np.round(order_quantity_tons, 2),
    
    # Inventory data
    'inventory_bandar_abbas_tons': np.round(inventory_bandar_abbas, 2),
    'inventory_tehran_tons': np.round(inventory_tehran, 2),
    'inventory_assaluyeh_tons': np.round(inventory_assaluyeh, 2),
    'total_inventory_tons': np.round(total_inventory, 2),
    
    # Price data
    'oil_price_usd_bbl': np.round(oil_price, 2),
    'price_hdpe_usd_ton': np.round(price_hdpe, 2),
    'price_pp_usd_ton': np.round(price_pp, 2),
    'feedstock_price_usd_ton': np.round(feedstock_price, 2),
    
    # Logistics data
    'ships_in_port': ships_in_port,
    'eta_days': eta_days,
    'logistics_cost_per_ton_usd': np.round(logistics_cost_per_ton, 2),
    
    # Performance indicators
    'warehouse_fill_rate_percent': np.round(warehouse_fill_rate, 2),
    'otif_rate_percent': np.round(otif_rate, 2),
    'operating_margin_percent': np.round(operating_margin, 2)
})

# ==============================================
# Save to CSV file
# ==============================================
output_file = "digital_value_chain_data_10k.csv"
df.to_csv(output_file, index=False)
print(f"✅ Value chain data saved successfully in file '{output_file}'.")
print(f"📊 Number of records: {len(df):,} - Number of variables: {len(df.columns)}")

print("\n🔍 Sample of generated data:")
print(df.head())

print("\n📈 Descriptive statistics of the data:")
print(df.describe(include='all'))

# Show the product distribution
print("\n📊 Distribution of product types:")
print(df['product_type'].value_counts())
📊 Sample output (first 5 records shown):
timestamp	orders_received	order_value_usd	product_type	order_quantity_tons	inventory_bandar_abbas_tons	...	oil_price_usd_bbl	price_hdpe_usd_ton	ships_in_port	eta_days	otif_rate_percent	operating_margin_percent
2026-07-22 08:00:00	2	152340.75	HDPE	245.30	5120.45	...	76.50	935.20	2	7.5	89.50	21.30
2026-07-22 08:00:01	1	98750.20	PP	180.50	5080.12	...	76.80	938.50	1	6.8	90.10	22.10
...	...	...	...	...	...	...	...	...	...	...	...	...
🔧 Technical implementation notes:
Sampling rate: timedelta(seconds=i) ensures the data are simulated at a rate of 1 record per second.

Data diversity: Includes a combination of continuous numeric data (prices), discrete numeric data (number of orders, ships) and qualitative data (product type).

Economic relationships: Product and feed prices are simulated as dependent on the oil price, which reflects the real world.

Performance indicators: Key indicators such as OTIF and profit margin are considered as evaluation criteria for value chain performance.

Real-world application: This data can be used to implement demand forecasting models, optimize inventory allocation, and analyze profit margins in the digital transformation platform.

💡 Suggestion for the next step:
After generating this data, you can:

Implement a demand forecasting model using Prophet or LSTM on historical order data.

Design a business intelligence (BI) dashboard with PowerBI or Tableau for real-time display of key indicators.

Implement a recommender system for optimal allocation of orders to warehouses based on the lowest shipping cost and nearest inventory



📄 SRS Document – Product 3: Digital Transformation and Value Chain Integration (Patentable)
1. Introduction
Purpose: Implement an integrated platform based on a Data Mesh architecture that connects the supply chain, production, distribution and sales of petrochemical products in real time and, using artificial intelligence, optimizes strategic and operational decision-making.

Patent innovation: Unlike the Honeywell patent, which emphasizes a centralized web-based platform, this system uses a Data Mesh architecture with decentralized data ownership and combines the supply, production, distribution and sales loops in an integrated optimization model.

2. Functional Requirements (with emphasis on patent capabilities)
ID	Requirement	Patent capability
FR-DATA-01	Integrate production, warehousing, transportation and sales data with a Data Mesh architecture (decentralized data ownership)	Industrial Data Mesh architecture (main innovation)
FR-ML-01	Simultaneous forecasting of demand and price and optimal feed allocation with the approach of maximizing the total profit margin of the holding	Integrated forecasting and optimization
FR-ML-02	Optimize feed allocation among production units with linear programming and LP algorithms	Resource allocation optimization
FR-LOG-01	Real-time shipment tracking with GPS and AIS and connection to Iranian customs and port systems	Localization of Iranian logistics
FR-BI-01	Automatic generation of "cost per ton of product" and "profit margin of each production unit" reports	Integrated profitability reporting
🧪 Synthetic Data Generation Code (integrated for all three domains)
The code below generates 10,000 records (1 record per second) for all three domains in an integrated way so it can be used to train the models of all three products.

python
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random

# ==============================================
# Data generation parameters
# ==============================================
NUM_RECORDS = 10000
START_TIME = datetime(2026, 7, 22, 8, 0, 0)

# ==============================================
# Generate timestamp (1 record per second)
# ==============================================
timestamps = [START_TIME + timedelta(seconds=i) for i in range(NUM_RECORDS)]
t = np.linspace(0, 10 * np.pi, NUM_RECORDS)  # for cyclic patterns

# ==============================================
# 1. Production optimization domain variables
# ==============================================

# Reactor temperature - range 150 to 350 degrees Celsius
reactor_temp = 250 + 30 * np.sin(t * 0.5) + 0.01 * np.arange(NUM_RECORDS) + np.random.normal(0, 2, NUM_RECORDS)
reactor_temp = np.clip(reactor_temp, 150, 350)

# Reactor pressure - range 10 to 40 bar
reactor_pressure = 25 + 5 * np.sin(t * 0.3) + 0.005 * np.arange(NUM_RECORDS) + np.random.normal(0, 0.8, NUM_RECORDS)
reactor_pressure = np.clip(reactor_pressure, 10, 40)

# Feed inlet flow - range 100 to 500 cubic meters per hour
feed_flow = 300 + 80 * np.sin(t * 0.2 + 1.2) + np.random.normal(0, 5, NUM_RECORDS)
feed_flow = np.clip(feed_flow, 100, 500)

# Product quality (MFI - melt flow index) - range 2 to 10
mfi_quality = 5 + 2 * np.sin(t * 0.3 + 0.5) + 0.002 * np.arange(NUM_RECORDS) + np.random.normal(0, 0.3, NUM_RECORDS)
mfi_quality = np.clip(mfi_quality, 2, 10)

# ==============================================
# 2. Energy and carbon management domain variables
# ==============================================

# Electricity consumption (instantaneous power) - range 5 to 25 megawatts
electricity_power = 15 + 5 * np.sin(t * 0.2) + 0.005 * np.arange(NUM_RECORDS) + np.random.normal(0, 0.5, NUM_RECORDS)
electricity_power = np.clip(electricity_power, 5, 25)

# Natural gas fuel consumption - range 50 to 150 thousand cubic meters per hour
fuel_gas_flow = 100 + 30 * np.sin(t * 0.15 + 1.5) + np.random.normal(0, 3, NUM_RECORDS)
fuel_gas_flow = np.clip(fuel_gas_flow, 50, 150)

# Steam consumption - range 10 to 50 tons per hour
steam_flow = 30 + 10 * np.sin(t * 0.25 + 0.8) + np.random.normal(0, 1.5, NUM_RECORDS)
steam_flow = np.clip(steam_flow, 10, 50)

# Scope 1 carbon emission - kg CO2 per ton of product
carbon_scope1 = 0.2 * fuel_gas_flow + 0.3 * steam_flow + np.random.normal(0, 2, NUM_RECORDS)
carbon_scope1 = np.clip(carbon_scope1, 20, 80)

# Scope 2 carbon emission (purchased electricity)
carbon_scope2 = 0.15 * electricity_power + np.random.normal(0, 1, NUM_RECORDS)
carbon_scope2 = np.clip(carbon_scope2, 5, 30)

# Scope 3 carbon emission (supply chain and distribution) - simulated
carbon_scope3 = 0.1 * feed_flow + 0.05 * np.random.randn(NUM_RECORDS) + 10
carbon_scope3 = np.clip(carbon_scope3, 5, 25)

# Total carbon emission
carbon_total = carbon_scope1 + carbon_scope2 + carbon_scope3

# ==============================================
# 3. Digital transformation and value chain domain variables
# ==============================================

# Crude oil price - range 60 to 90 dollars per barrel
oil_price = 75 + 5 * np.sin(t * 0.15) + 2 * np.random.randn(NUM_RECORDS)
oil_price = np.clip(oil_price, 60, 90)

# Product price (HDPE) - dependent on oil price
price_hdpe = 900 + 0.5 * (oil_price - 75) * 10 + 20 * np.sin(t * 0.2) + 5 * np.random.randn(NUM_RECORDS)
price_hdpe = np.clip(price_hdpe, 750, 1100)

# Number of orders received (Poisson distribution)
orders_received = np.random.poisson(lam=2, size=NUM_RECORDS)

# Warehouse inventory - range 2000 to 8000 tons
inventory = 5000 + 1000 * np.sin(t * 0.2) + np.random.normal(0, 100, NUM_RECORDS)
inventory = np.clip(inventory, 2000, 8000)

# Delivery time (ETA) - range 2 to 15 days
eta_days = 7 + 3 * np.sin(t * 0.15) + 2 * np.random.randn(NUM_RECORDS)
eta_days = np.clip(np.round(eta_days, 1), 2, 15)

# ==============================================
# 4. Target variables (main outputs)
# ==============================================

# Production efficiency (Efficiency) - a function of temperature and pressure
production_efficiency = ((reactor_temp - 200) / 150 * 20 + (reactor_pressure - 20) / 20 * 10 + 60 
                         + np.random.normal(0, 2, NUM_RECORDS))
production_efficiency = np.clip(production_efficiency, 40, 98)

# Energy intensity (SEC) - range 500 to 800 kg crude oil equivalent per ton
energy_intensity = (600 + 0.5 * fuel_gas_flow + 2 * steam_flow - 0.1 * feed_flow 
                    + 0.3 * reactor_temp + np.random.normal(0, 10, NUM_RECORDS))
energy_intensity = np.clip(energy_intensity, 500, 800)

# Operating profit margin - percent
operating_margin = 20 + 3 * np.sin(t * 0.2 + 1.0) + 2 * np.random.randn(NUM_RECORDS)
operating_margin = np.clip(operating_margin, 10, 35)

# ==============================================
# Build the integrated dataframe
# ==============================================
df = pd.DataFrame({
    'timestamp': timestamps,
    
    # Domain 1: Production optimization
    'reactor_temp_c': np.round(reactor_temp, 2),
    'reactor_pressure_bar': np.round(reactor_pressure, 2),
    'feed_flow_m3h': np.round(feed_flow, 2),
    'mfi_quality': np.round(mfi_quality, 2),
    'production_efficiency_percent': np.round(production_efficiency, 2),
    
    # Domain 2: Energy and carbon management
    'electricity_power_mw': np.round(electricity_power, 2),
    'fuel_gas_flow_km3h': np.round(fuel_gas_flow, 2),
    'steam_flow_tonh': np.round(steam_flow, 2),
    'carbon_scope1_kgco2_ton': np.round(carbon_scope1, 2),
    'carbon_scope2_kgco2_ton': np.round(carbon_scope2, 2),
    'carbon_scope3_kgco2_ton': np.round(carbon_scope3, 2),
    'carbon_total_kgco2_ton': np.round(carbon_total, 2),
    'energy_intensity_kgoe_ton': np.round(energy_intensity, 2),
    
    # Domain 3: Digital transformation and value chain
    'oil_price_usd_bbl': np.round(oil_price, 2),
    'price_hdpe_usd_ton': np.round(price_hdpe, 2),
    'orders_received': orders_received,
    'inventory_tons': np.round(inventory, 2),
    'eta_days': eta_days,
    'operating_margin_percent': np.round(operating_margin, 2)
})

# ==============================================
# Save the file
# ==============================================
output_file = "integrated_petrochemical_data_10k.csv"
df.to_csv(output_file, index=False)
print(f"✅ Integrated data saved in file '{output_file}'.")
print(f"📊 Number of records: {len(df):,} - Number of variables: {len(df.columns)}")

print("\n🔍 Sample of generated data:")
print(df.head())

print("\n📈 Descriptive statistics of the data:")
print(df.describe())
🧩 Summary: Key Patentable Capabilities
Domain	Innovative capabilities for patenting
Production optimization	1. Intelligent virtual sensors for real-time prediction of product properties
2. Three-objective optimization (cost, quality, energy) with PSO
3. Synthetic data generation with GAN for training under low-data conditions
Energy and carbon management	1. Complete Scope 1, 2 and 3 calculation (unlike existing patents)
2. Carbon-oriented what-if scenario simulation
3. Localization for Iranian regulations and emission factors
Digital transformation	1. Industrial Data Mesh architecture with decentralized data ownership
2. Integrated forecasting and optimization of the entire value chain
3. Connection to Iranian customs and port systems

