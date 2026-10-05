# Patent Claims — Product 3: Digital Transformation and Value Chain Integration

## Proposed Title
An integrated petrochemical value chain optimization system based on a decentralized Data Mesh architecture with simultaneous demand/price forecasting and optimal feed allocation to maximize the total profit margin of the holding, along with localization of Iranian port and customs logistics.

## Differentiation from Prior Art (including centralized web-based platforms such as Honeywell)
1. Decentralized data ownership (Data Mesh) per subsidiary with an independent topic and domain owner.
2. An integrated optimization loop of demand + price + feed allocation (LP) with the holding's total margin as the objective function.
3. Localization of AIS/GPS tracking and connection to Iranian customs declaration/port codes.
4. Integrated reporting of cost per ton and margin of each production unit in a multilingual Command Center.
5. AES-256-GCM encryption for sensitive price/contract data and TLS 1.3 transport.

## Proposed Claims (brief)
### Claim 1 (main)
A method for integrating the petrochemical value chain comprising:
- extracting data from multiple OLTP/ERP sources,
- standardizing the product identifier (HS) and unit of measurement,
- publishing events on a dedicated topic of each data domain,
- running an integrated demand-price-feed optimization to maximize the holding's total margin.

### Claim 2
The Claim 1 system that implements data ownership in a decentralized manner (Data Mesh) with lineage recording for each subsidiary.

### Claim 3
The Claim 1 system that solves feed allocation with linear programming under unit capacity constraints and forecast demand.

### Claim 4
The Claim 1 system that performs shipment tracking with AIS/GPS and ETA calculation based on port traffic and Persian Gulf/Oman Sea weather conditions, and links to the Iranian customs declaration.

### Claim 5
The Claim 1 system that stores sensitive price/contract data with AES-256-GCM, requires TLS 1.3 for transport, and records events in an audit log.

## Mapping to the Current Implementation
| Claim | Module |
|------|--------|
| 1-2 | `services/data-integration` |
| 1,3 | `services/supply-chain-analytics` |
| 4 | `services/logistics` |
| 1 | `services/order-to-cash` + `services/bi-reporting` |
| 5 | `shared/crypto.py`, `infra/nginx`, `shared/audit.py` |

## Demo PoC
```bash
python scripts/demo_patent_poc.py
python scripts/security_scan.py
python scripts/generate_tls_certs.py
# Optional with running services:
python scripts/load_test.py --requests 200 --concurrency 32
```

## Target Non-Functional Criteria
- Dashboard response < 2s
- 3-month demand forecast < 5min
- Availability 99.95%
- Horizontal scaling of the critical path up to 50,000 TPS (with replicas)
- AES-256 at-rest + TLS 1.3 in-transit
