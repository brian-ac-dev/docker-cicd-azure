from __future__ import annotations

import random
from datetime import datetime, timedelta

CATEGORIES = [
    "Electrónica",
    "Hogar",
    "Deportes",
    "Libros",
    "Jardín",
    "Moda",
    "Juguetes",
    "Automoción",
]

CITIES = [
    "Madrid",
    "Barcelona",
    "Valencia",
    "Sevilla",
    "Bilbao",
    "Zaragoza",
    "Málaga",
    "Murcia",
]

FIRST_NAMES = [
    "Ana",
    "Luis",
    "María",
    "Carlos",
    "Elena",
    "Jorge",
    "Lucía",
    "Pablo",
    "Sofía",
    "Diego",
]

LAST_NAMES = [
    "García",
    "Martínez",
    "López",
    "Sánchez",
    "Pérez",
    "González",
    "Rodríguez",
    "Fernández",
    "Torres",
    "Ruiz",
]

STATUSES = ["activo", "inactivo", "pendiente", "archivado"]
ORDER_STATUSES = ["nuevo", "procesando", "enviado", "entregado", "cancelado"]


def _seeded_rng(label: str) -> random.Random:
    return random.Random(hash(label) & 0xFFFFFFFF)


def build_products(count: int = 180) -> list[dict]:
    rng = _seeded_rng("products")
    products = []
    for index in range(1, count + 1):
        category = rng.choice(CATEGORIES)
        price = round(rng.uniform(4.5, 899.99), 2)
        stock = rng.randint(0, 500)
        products.append(
            {
                "id": f"PRD-{index:04d}",
                "name": f"{category} demo #{index}",
                "category": category,
                "price_eur": price,
                "stock": stock,
                "sku": f"SKU-{index:05d}",
                "updated_at": (
                    datetime(2026, 1, 1) + timedelta(days=rng.randint(0, 170))
                ).strftime("%Y-%m-%d"),
            }
        )
    return products


def build_customers(count: int = 120) -> list[dict]:
    rng = _seeded_rng("customers")
    customers = []
    for index in range(1, count + 1):
        first = rng.choice(FIRST_NAMES)
        last = rng.choice(LAST_NAMES)
        customers.append(
            {
                "id": f"CUS-{index:04d}",
                "name": f"{first} {last}",
                "email": f"{first.lower()}.{last.lower()}{index}@demo.local",
                "city": rng.choice(CITIES),
                "status": rng.choice(STATUSES),
                "orders": rng.randint(0, 42),
                "since": (datetime(2020, 1, 1) + timedelta(days=rng.randint(0, 2200))).strftime(
                    "%Y-%m-%d"
                ),
            }
        )
    return customers


def build_orders(count: int = 250) -> list[dict]:
    rng = _seeded_rng("orders")
    orders = []
    for index in range(1, count + 1):
        amount = round(rng.uniform(12.0, 1450.0), 2)
        orders.append(
            {
                "id": f"ORD-{index:05d}",
                "customer_id": f"CUS-{rng.randint(1, 120):04d}",
                "product_id": f"PRD-{rng.randint(1, 180):04d}",
                "amount_eur": amount,
                "items": rng.randint(1, 8),
                "status": rng.choice(ORDER_STATUSES),
                "created_at": (
                    datetime(2025, 6, 1) + timedelta(hours=rng.randint(0, 8000))
                ).strftime("%Y-%m-%d %H:%M"),
            }
        )
    return sorted(orders, key=lambda row: row["created_at"], reverse=True)


PRODUCTS = build_products()
CUSTOMERS = build_customers()
ORDERS = build_orders()

_PRODUCTS_BY_ID = {product["id"]: product for product in PRODUCTS}


def get_dashboard_stats() -> dict:
    revenue = sum(order["amount_eur"] for order in ORDERS)
    delivered = sum(1 for order in ORDERS if order["status"] == "entregado")
    categories: dict[str, int] = {}
    for product in PRODUCTS:
        categories[product["category"]] = categories.get(product["category"], 0) + 1
    top_category = max(categories, key=categories.get)

    return {
        "revenue_eur": round(revenue, 2),
        "avg_order_eur": round(revenue / len(ORDERS), 2),
        "delivered_pct": round(delivered / len(ORDERS) * 100),
        "top_category": top_category,
    }


def get_featured_product(day: datetime | None = None) -> dict:
    day = day or datetime.now()
    index = day.timetuple().tm_yday % len(PRODUCTS)
    return PRODUCTS[index]


def get_recent_orders(limit: int = 5) -> list[dict]:
    recent = []
    for order in ORDERS[:limit]:
        product = _PRODUCTS_BY_ID.get(order["product_id"], {})
        recent.append({**order, "product_name": product.get("name", "—")})
    return recent
