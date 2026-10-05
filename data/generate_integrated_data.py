"""
Generate integrated data for three domains:
1) Production optimization  2) Energy and carbon management  3) Digital transformation / value chain
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
    t = np.linspace(0, 10 * np.pi, num_records)

    reactor_temp = 250 + 30 * np.sin(t * 0.5) + 0.01 * np.arange(num_records) + rng.normal(0, 2, num_records)
    reactor_temp = np.clip(reactor_temp, 150, 350)

    reactor_pressure = (
        25 + 5 * np.sin(t * 0.3) + 0.005 * np.arange(num_records) + rng.normal(0, 0.8, num_records)
    )
    reactor_pressure = np.clip(reactor_pressure, 10, 40)

    feed_flow = 300 + 80 * np.sin(t * 0.2 + 1.2) + rng.normal(0, 5, num_records)
    feed_flow = np.clip(feed_flow, 100, 500)

    mfi_quality = 5 + 2 * np.sin(t * 0.3 + 0.5) + 0.002 * np.arange(num_records) + rng.normal(0, 0.3, num_records)
    mfi_quality = np.clip(mfi_quality, 2, 10)

    electricity_power = 15 + 5 * np.sin(t * 0.2) + 0.005 * np.arange(num_records) + rng.normal(0, 0.5, num_records)
    electricity_power = np.clip(electricity_power, 5, 25)

    fuel_gas_flow = 100 + 30 * np.sin(t * 0.15 + 1.5) + rng.normal(0, 3, num_records)
    fuel_gas_flow = np.clip(fuel_gas_flow, 50, 150)

    steam_flow = 30 + 10 * np.sin(t * 0.25 + 0.8) + rng.normal(0, 1.5, num_records)
    steam_flow = np.clip(steam_flow, 10, 50)

    carbon_scope1 = 0.2 * fuel_gas_flow + 0.3 * steam_flow + rng.normal(0, 2, num_records)
    carbon_scope1 = np.clip(carbon_scope1, 20, 80)
    carbon_scope2 = 0.15 * electricity_power + rng.normal(0, 1, num_records)
    carbon_scope2 = np.clip(carbon_scope2, 5, 30)
    carbon_scope3 = 0.1 * feed_flow + 0.05 * rng.standard_normal(num_records) + 10
    carbon_scope3 = np.clip(carbon_scope3, 5, 25)
    carbon_total = carbon_scope1 + carbon_scope2 + carbon_scope3

    oil_price = 75 + 5 * np.sin(t * 0.15) + 2 * rng.standard_normal(num_records)
    oil_price = np.clip(oil_price, 60, 90)
    price_hdpe = (
        900 + 0.5 * (oil_price - 75) * 10 + 20 * np.sin(t * 0.2) + 5 * rng.standard_normal(num_records)
    )
    price_hdpe = np.clip(price_hdpe, 750, 1100)

    orders_received = rng.poisson(lam=2, size=num_records)
    inventory = 5000 + 1000 * np.sin(t * 0.2) + rng.normal(0, 100, num_records)
    inventory = np.clip(inventory, 2000, 8000)
    eta_days = 7 + 3 * np.sin(t * 0.15) + 2 * rng.standard_normal(num_records)
    eta_days = np.clip(np.round(eta_days, 1), 2, 15)

    production_efficiency = (
        (reactor_temp - 200) / 150 * 20
        + (reactor_pressure - 20) / 20 * 10
        + 60
        + rng.normal(0, 2, num_records)
    )
    production_efficiency = np.clip(production_efficiency, 40, 98)

    energy_intensity = (
        600
        + 0.5 * fuel_gas_flow
        + 2 * steam_flow
        - 0.1 * feed_flow
        + 0.3 * reactor_temp
        + rng.normal(0, 10, num_records)
    )
    energy_intensity = np.clip(energy_intensity, 500, 800)

    operating_margin = 20 + 3 * np.sin(t * 0.2 + 1.0) + 2 * rng.standard_normal(num_records)
    operating_margin = np.clip(operating_margin, 10, 35)

    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "reactor_temp_c": np.round(reactor_temp, 2),
            "reactor_pressure_bar": np.round(reactor_pressure, 2),
            "feed_flow_m3h": np.round(feed_flow, 2),
            "mfi_quality": np.round(mfi_quality, 2),
            "production_efficiency_percent": np.round(production_efficiency, 2),
            "electricity_power_mw": np.round(electricity_power, 2),
            "fuel_gas_flow_km3h": np.round(fuel_gas_flow, 2),
            "steam_flow_tonh": np.round(steam_flow, 2),
            "carbon_scope1_kgco2_ton": np.round(carbon_scope1, 2),
            "carbon_scope2_kgco2_ton": np.round(carbon_scope2, 2),
            "carbon_scope3_kgco2_ton": np.round(carbon_scope3, 2),
            "carbon_total_kgco2_ton": np.round(carbon_total, 2),
            "energy_intensity_kgoe_ton": np.round(energy_intensity, 2),
            "oil_price_usd_bbl": np.round(oil_price, 2),
            "price_hdpe_usd_ton": np.round(price_hdpe, 2),
            "orders_received": orders_received,
            "inventory_tons": np.round(inventory, 2),
            "eta_days": eta_days,
            "operating_margin_percent": np.round(operating_margin, 2),
        }
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate integrated petrochemical data")
    parser.add_argument("--num-records", type=int, default=10_000)
    parser.add_argument("--start-time", type=str, default="2026-07-22T08:00:00")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent / "integrated_petrochemical_data_10k.csv",
    )
    args = parser.parse_args()

    start = datetime.fromisoformat(args.start_time)
    df = generate_dataset(args.num_records, start, args.seed)
    df.to_csv(args.output, index=False)
    print(f"✅ Integrated data saved in '{args.output}'.")
    print(f"📊 Number of records: {len(df):,} - Number of variables: {len(df.columns)}")
    print(df.head())


if __name__ == "__main__":
    main()
