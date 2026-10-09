"""Idempotently load a small CA_1/FOODS M5 demo catalog through d_1913.

Raw M5 files are deliberately local/ignored.  This utility never reads
``d_1914:d_1941`` demand, so it cannot use held-out TEST actuals as input.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.db.database import SessionLocal
from backend.app.db.models import Category, Inventory, Product, SalesDaily


ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/raw/m5"
ITEM_IDS = ("FOODS_1_001", "FOODS_1_002", "FOODS_2_001", "FOODS_2_002", "FOODS_3_001")
DEMO_CATEGORY = "M5_DEMO_FOODS"


def main() -> None:
    calendar_path = RAW / "calendar.csv"
    sales_path = RAW / "sales_train_evaluation.csv"
    prices_path = RAW / "sell_prices.csv"
    if not all(path.is_file() for path in (calendar_path, sales_path, prices_path)):
        raise RuntimeError("M5 demo import requires local ignored calendar, evaluation-sales, and price CSV files")
    days = [f"d_{index}" for index in range(1, 1914)]
    sales = pd.read_csv(sales_path, usecols=["item_id", "dept_id", "store_id", *days])
    sales = sales.loc[(sales["store_id"] == "CA_1") & sales["item_id"].isin(ITEM_IDS)].set_index("item_id")
    if set(ITEM_IDS).difference(sales.index):
        raise RuntimeError("the deterministic M5 demo SKU selection was not found in CA_1 evaluation sales")
    calendar = pd.read_csv(calendar_path, usecols=["d", "date", "wm_yr_wk"]).iloc[:1913]
    calendar["date"] = pd.to_datetime(calendar["date"]).dt.date
    price_chunks = []
    for chunk in pd.read_csv(prices_path, chunksize=100_000):
        matched = chunk.loc[(chunk["store_id"] == "CA_1") & chunk["item_id"].isin(ITEM_IDS), ["item_id", "wm_yr_wk", "sell_price"]]
        if not matched.empty:
            price_chunks.append(matched)
    weekly_prices = pd.concat(price_chunks).pivot(index="item_id", columns="wm_yr_wk", values="sell_price")
    with SessionLocal.begin() as session:
        category = session.scalar(select(Category).where(Category.code == DEMO_CATEGORY))
        if category is None:
            category = Category(code=DEMO_CATEGORY, name="M5 CA_1 FOODS demo")
            session.add(category)
            session.flush()
        for item_id in ITEM_IDS:
            product = session.scalar(select(Product).where(Product.sku == item_id))
            if product is None:
                product = Product(sku=item_id, name=f"Demo Product — {item_id}", category_id=category.id, unit="unit", is_active=True)
                session.add(product)
                session.flush()
                session.add(Inventory(product_id=product.id, on_hand=0))
            existing = {row.sale_date: row for row in session.scalars(select(SalesDaily).where(SalesDaily.product_id == product.id, SalesDaily.sale_date >= calendar["date"].iloc[0], SalesDaily.sale_date <= calendar["date"].iloc[-1]))}
            quantities = sales.loc[item_id, days].to_numpy(dtype=int)
            prices = weekly_prices.reindex(index=[item_id], columns=calendar["wm_yr_wk"].to_numpy()).to_numpy(dtype=float)[0]
            for sale_date, quantity, price in zip(calendar["date"], quantities, prices, strict=True):
                row = existing.get(sale_date)
                if row is None:
                    session.add(SalesDaily(product_id=product.id, sale_date=sale_date, quantity_sold=int(quantity), sell_price=None if np.isnan(price) else float(price), source="M5_CA1_FOODS_DEMO"))
                else:
                    row.quantity_sold = int(quantity)
                    row.sell_price = None if np.isnan(price) else float(price)
                    row.source = "M5_CA1_FOODS_DEMO"
    print(f"M5 demo import complete: {len(ITEM_IDS)} products, {len(ITEM_IDS) * len(days)} daily rows through d_1913.")


if __name__ == "__main__":
    main()
