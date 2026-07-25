"""
تولید داده‌های سنتتیک زنجیره ارزش (سفارش، موجودی، قیمت، لجستیک، KPI).

۱۰٬۰۰۰ رکورد با نرخ ۱ رکورد در ثانیه مطابق README / SRS محصول ۳.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def generate_dataset(num_records: int, start_time: datetime, seed: int | None = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    timestamps = [start_time + timedelta(seconds=i) for i in range(num_records)]

    orders_received = rng.poisson(lam=2, size=num_records)
    order_value = rng.uniform(10000, 250000, size=num_records)
    product_types = rng.choice(
        ["HDPE", "LDPE", "LLDPE", "PP", "PET"], size=num_records, p=[0.3, 0.2, 0.2, 0.2, 0.1]
    )
    order_quantity_tons = rng.uniform(20, 500, size=num_records)

    inventory_bandar_abbas = 5000 + 1000 * np.sin(np.linspace(0, 4 * np.pi, num_records)) + rng.normal(
        0, 100, num_records
    )
    inventory_bandar_abbas = np.clip(inventory_bandar_abbas, 2000, 8000)

    inventory_tehran = 3000 + 800 * np.sin(np.linspace(0, 4 * np.pi, num_records) + 1.5) + rng.normal(
        0, 80, num_records
    )
    inventory_tehran = np.clip(inventory_tehran, 1000, 6000)

    inventory_assaluyeh = 8000 + 1500 * np.sin(np.linspace(0, 4 * np.pi, num_records) + 3.0) + rng.normal(
        0, 150, num_records
    )
    inventory_assaluyeh = np.clip(inventory_assaluyeh, 4000, 12000)
    total_inventory = inventory_bandar_abbas + inventory_tehran + inventory_assaluyeh

    oil_price = 75 + 5 * np.sin(np.linspace(0, 3 * np.pi, num_records)) + 2 * rng.standard_normal(num_records)
    oil_price = np.clip(oil_price, 60, 90)

    price_hdpe = (
        900
        + 0.5 * (oil_price - 75) * 10
        + 20 * np.sin(np.linspace(0, 2 * np.pi, num_records))
        + 5 * rng.standard_normal(num_records)
    )
    price_hdpe = np.clip(price_hdpe, 750, 1100)

    price_pp = (
        850
        + 0.4 * (oil_price - 75) * 10
        + 25 * np.sin(np.linspace(0, 2 * np.pi, num_records) + 1.0)
        + 5 * rng.standard_normal(num_records)
    )
    price_pp = np.clip(price_pp, 700, 1050)

    feedstock_price = (
        800
        + 0.3 * (oil_price - 75) * 10
        + 15 * np.sin(np.linspace(0, 2 * np.pi, num_records) + 2.0)
        + 5 * rng.standard_normal(num_records)
    )
    feedstock_price = np.clip(feedstock_price, 700, 1000)

    ships_in_port = rng.choice([0, 1, 2, 3, 4], size=num_records, p=[0.1, 0.25, 0.35, 0.2, 0.1])
    eta_days = 7 + 3 * np.sin(np.linspace(0, 2 * np.pi, num_records)) + 2 * rng.standard_normal(num_records)
    eta_days = np.clip(np.round(eta_days, 1), 2, 15)

    logistics_cost_per_ton = 50 + 0.2 * (oil_price - 75) + 10 * rng.standard_normal(num_records)
    logistics_cost_per_ton = np.clip(logistics_cost_per_ton, 30, 80)

    warehouse_fill_rate = 70 + 10 * np.sin(np.linspace(0, 2 * np.pi, num_records)) + 5 * rng.standard_normal(
        num_records
    )
    warehouse_fill_rate = np.clip(warehouse_fill_rate, 40, 95)

    otif_rate = (
        88 + 5 * np.sin(np.linspace(0, 2 * np.pi, num_records) + 0.5) + 3 * rng.standard_normal(num_records)
    )
    otif_rate = np.clip(otif_rate, 70, 99)

    operating_margin = (
        20 + 3 * np.sin(np.linspace(0, 2 * np.pi, num_records) + 1.0) + 2 * rng.standard_normal(num_records)
    )
    operating_margin = np.clip(operating_margin, 10, 35)

    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "orders_received": orders_received,
            "order_value_usd": np.round(order_value, 2),
            "product_type": product_types,
            "order_quantity_tons": np.round(order_quantity_tons, 2),
            "inventory_bandar_abbas_tons": np.round(inventory_bandar_abbas, 2),
            "inventory_tehran_tons": np.round(inventory_tehran, 2),
            "inventory_assaluyeh_tons": np.round(inventory_assaluyeh, 2),
            "total_inventory_tons": np.round(total_inventory, 2),
            "oil_price_usd_bbl": np.round(oil_price, 2),
            "price_hdpe_usd_ton": np.round(price_hdpe, 2),
            "price_pp_usd_ton": np.round(price_pp, 2),
            "feedstock_price_usd_ton": np.round(feedstock_price, 2),
            "ships_in_port": ships_in_port,
            "eta_days": eta_days,
            "logistics_cost_per_ton_usd": np.round(logistics_cost_per_ton, 2),
            "warehouse_fill_rate_percent": np.round(warehouse_fill_rate, 2),
            "otif_rate_percent": np.round(otif_rate, 2),
            "operating_margin_percent": np.round(operating_margin, 2),
        }
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="تولید داده سنتتیک زنجیره ارزش")
    parser.add_argument("--num-records", type=int, default=10_000)
    parser.add_argument("--start-time", type=str, default="2026-07-22T08:00:00")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent / "digital_value_chain_data_10k.csv",
    )
    args = parser.parse_args()

    start = datetime.fromisoformat(args.start_time)
    df = generate_dataset(args.num_records, start, args.seed)
    df.to_csv(args.output, index=False)
    print(f"✅ داده‌های زنجیره ارزش در '{args.output}' ذخیره شد.")
    print(f"📊 تعداد رکوردها: {len(df):,} - تعداد متغیرها: {len(df.columns)}")
    print(df.head())
    print(df["product_type"].value_counts())


if __name__ == "__main__":
    main()
