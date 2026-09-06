from __future__ import annotations

import os
import platform
import socket
import sys
import time
from datetime import datetime, timezone

from flask import Blueprint, jsonify, render_template

from app.demo_data import CUSTOMERS, ORDERS, PRODUCTS, get_dashboard_stats, get_featured_product, get_recent_orders

bp = Blueprint("main", __name__)

STARTED_AT = datetime.now(timezone.utc)
PROCESS_START = time.time()


def _greeting() -> str:
    hour = datetime.now().hour
    if hour < 12:
        return "Buenos días"
    if hour < 19:
        return "Buenas tardes"
    return "Buenas noches"


def _uptime() -> str:
    uptime_seconds = int(time.time() - PROCESS_START)
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


@bp.route("/")
def index():
    return render_template(
        "index.html",
        greeting=_greeting(),
        stats=get_dashboard_stats(),
        featured=get_featured_product(),
        recent_orders=get_recent_orders(),
        product_count=len(PRODUCTS),
        customer_count=len(CUSTOMERS),
        order_count=len(ORDERS),
        build_tag=os.environ.get("BUILD_TAG", "local"),
    )


@bp.route("/productos")
def products():
    return render_template("products.html", products=PRODUCTS)


@bp.route("/clientes")
def customers():
    return render_template("customers.html", customers=CUSTOMERS)


@bp.route("/pedidos")
def orders():
    return render_template("orders.html", orders=ORDERS)


@bp.route("/health")
def health():
    return jsonify(
        {
            "status": "ok",
            "app": os.environ.get("APP_NAME", "PopShop"),
            "version": os.environ.get("APP_VERSION", "1.1.0"),
            "build": os.environ.get("BUILD_TAG", "local"),
            "uptime": _uptime(),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }
    )


@bp.route("/runtime")
def runtime():
    info = {
        "app_name": os.environ.get("APP_NAME", "PopShop"),
        "app_version": os.environ.get("APP_VERSION", "1.1.0"),
        "build_tag": os.environ.get("BUILD_TAG", "local"),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "hostname": socket.gethostname(),
        "pid": os.getpid(),
        "cwd": os.getcwd(),
        "flask_env": os.environ.get("FLASK_ENV", "production"),
        "port": os.environ.get("PORT", "5000"),
        "started_at_utc": STARTED_AT.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "server_time_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "uptime": _uptime(),
        "executable": sys.executable,
    }

    return render_template("runtime.html", info=info)
