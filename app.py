"""
Smart Shopping Intelligence System — Main Flask Application.
Connects SQLite storage, session cart/authentication, Apriori ML recommender,
and Plotly analytics dashboard.
"""

import os
import re
from typing import Any

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import (
    create_user,
    get_all_products,
    get_categories_summary,
    get_product_by_id,
    get_products_by_ids,
    get_user_by_email,
    get_user_by_id,
    get_user_transactions,
    init_db,
    save_checkout_transaction,
)
from ml.analytics import compute_dashboard_analytics
from ml.recommendation import recommender_engine

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
TAX_RATE = 0.05


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "smart-shopping-intelligence-dev-key-2026")

    # Initialize database & train initial Apriori ML engine
    init_db()
    recommender_engine.train()

    def _get_cart_dict() -> dict[str, int]:
        cart = session.get("cart", {})
        if not isinstance(cart, dict):
            cart = {}
        return {str(k): int(v) for k, v in cart.items() if int(v) > 0}

    def _build_cart_payload() -> dict[str, Any]:
        cart_map = _get_cart_dict()
        if not cart_map:
            return {
                "items": [],
                "item_count": 0,
                "subtotal": 0.0,
                "tax": 0.0,
                "total": 0.0,
                "recommendations": [],
                "rec_message": "Add products to your cart to unlock AI basket recommendations.",
            }

        ids = [int(pid) for pid in cart_map.keys() if pid.isdigit()]
        products = get_products_by_ids(ids)
        product_by_id = {p["id"]: p for p in products}

        items = []
        subtotal = 0.0
        total_qty = 0
        cart_names = []

        for pid_str, qty in cart_map.items():
            if not pid_str.isdigit():
                continue
            pid = int(pid_str)
            prod = product_by_id.get(pid)
            if not prod:
                continue
            line_total = round(float(prod["price"]) * qty, 2)
            subtotal += line_total
            total_qty += qty
            cart_names.append(prod["name"])
            items.append(
                {
                    **prod,
                    "quantity": qty,
                    "line_total": line_total,
                }
            )

        subtotal = round(subtotal, 2)
        tax = round(subtotal * TAX_RATE, 2)
        total = round(subtotal + tax, 2)

        rec_result = recommender_engine.recommend_for_items(cart_names, top_n=4)

        return {
            "items": items,
            "item_count": total_qty,
            "subtotal": subtotal,
            "tax": tax,
            "total": total,
            "recommendations": rec_result["recommendations"],
            "rec_message": rec_result["message"],
        }

    @app.context_processor
    def inject_globals() -> dict[str, Any]:
        user = None
        if session.get("user_id"):
            user = get_user_by_id(int(session["user_id"]))
            if not user:
                session.pop("user_id", None)
        cart_map = _get_cart_dict()
        cart_count = sum(cart_map.values())
        return {
            "current_user": user,
            "cart_count": cart_count,
        }

    # ----------------- Pages -----------------

    @app.route("/")
    def index():
        all_products = get_all_products()
        featured_products = [p for p in all_products if p["featured"]][:6]
        categories = get_categories_summary()
        top_rules = recommender_engine.get_top_rules(limit=4)
        model_stats = recommender_engine.summary()
        return render_template(
            "index.html",
            featured_products=featured_products,
            categories=categories,
            top_rules=top_rules,
            model_stats=model_stats,
        )

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if session.get("user_id"):
            return redirect(url_for("products"))

        errors: dict[str, str] = {}
        email_val = ""

        if request.method == "POST":
            email_val = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")

            if not email_val or not EMAIL_REGEX.match(email_val):
                errors["email"] = "Please enter a valid email address."
            if not password:
                errors["password"] = "Please enter your password."

            if not errors:
                user = get_user_by_email(email_val)
                if not user or not check_password_hash(user["password_hash"], password):
                    errors["form"] = "Invalid email or password. Please check your credentials."
                else:
                    session["user_id"] = user["id"]
                    flash(f"Welcome back, {user['full_name']}!", "success")
                    next_url = request.args.get("next")
                    if next_url and next_url.startswith("/"):
                        return redirect(next_url)
                    return redirect(url_for("products"))

        return render_template("login.html", errors=errors, email_val=email_val)

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if session.get("user_id"):
            return redirect(url_for("products"))

        errors: dict[str, str] = {}
        form_data = {"full_name": "", "email": ""}

        if request.method == "POST":
            full_name = request.form.get("full_name", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            confirm_password = request.form.get("confirm_password", "")

            form_data = {"full_name": full_name, "email": email}

            if len(full_name) < 2:
                errors["full_name"] = "Full name must be at least 2 characters."
            if not email or not EMAIL_REGEX.match(email):
                errors["email"] = "Please provide a valid email address."
            if len(password) < 6:
                errors["password"] = "Password must be at least 6 characters long."
            if password != confirm_password:
                errors["confirm_password"] = "Passwords do not match."

            if not errors:
                pw_hash = generate_password_hash(password)
                user_id = create_user(full_name, email, pw_hash)
                if user_id is None:
                    errors["email"] = "An account with this email already exists."
                else:
                    session["user_id"] = user_id
                    flash("Account created successfully! Welcome to SmartShop AI.", "success")
                    return redirect(url_for("products"))

        return render_template("register.html", errors=errors, form_data=form_data)

    @app.route("/logout")
    def logout():
        session.pop("user_id", None)
        flash("You have been signed out cleanly.", "info")
        return redirect(url_for("index"))

    @app.route("/products")
    def products():
        search = request.args.get("q", "").strip()
        category = request.args.get("category", "All").strip()
        sort_by = request.args.get("sort", "featured").strip()

        product_list = get_all_products(search=search, category=category, sort_by=sort_by)
        categories = get_categories_summary()
        return render_template(
            "products.html",
            products=product_list,
            categories=categories,
            selected_category=category,
            search_query=search,
            sort_by=sort_by,
        )

    @app.route("/product/<int:product_id>")
    def product_detail(product_id: int):
        product = get_product_by_id(product_id)
        if not product:
            flash("Product not found.", "warning")
            return redirect(url_for("products"))

        rec_result = recommender_engine.recommend_for_items([product["name"]], top_n=4)
        return render_template(
            "product_detail.html",
            product=product,
            recommendations=rec_result["recommendations"],
            rec_message=rec_result["message"],
        )

    @app.route("/cart")
    def cart():
        cart_data = _build_cart_payload()
        past_orders = []
        if session.get("user_id"):
            past_orders = get_user_transactions(int(session["user_id"]), limit=5)
        return render_template("cart.html", cart=cart_data, past_orders=past_orders)

    @app.route("/recommendations")
    def recommendations():
        all_products = get_all_products(sort_by="name")
        initial_item = request.args.get("item", "Bread").strip()
        if not any(p["name"] == initial_item for p in all_products):
            initial_item = "Bread"
        initial_result = recommender_engine.recommend_for_items([initial_item], top_n=6)
        top_rules = recommender_engine.get_top_rules(limit=15)
        frequent_itemsets = recommender_engine.get_frequent_itemsets(min_len=2, limit=12)
        return render_template(
            "recommendations.html",
            products=all_products,
            initial_item=initial_item,
            initial_result=initial_result,
            top_rules=top_rules,
            frequent_itemsets=frequent_itemsets,
            model_stats=recommender_engine.summary(),
        )

    @app.route("/dashboard")
    def dashboard():
        analytics = compute_dashboard_analytics()
        return render_template("dashboard.html", analytics=analytics)

    @app.route("/about")
    def about():
        model_stats = recommender_engine.summary()
        return render_template("about.html", model_stats=model_stats)

    # ----------------- REST / AJAX APIs -----------------

    @app.route("/api/products")
    def api_products():
        search = request.args.get("q", "").strip()
        category = request.args.get("category", "All").strip()
        sort_by = request.args.get("sort", "featured").strip()
        items = get_all_products(search=search, category=category, sort_by=sort_by)
        return jsonify({"products": items, "count": len(items)})

    @app.route("/api/products/<int:product_id>")
    def api_product_detail(product_id: int):
        product = get_product_by_id(product_id)
        if not product:
            return jsonify({"error": "Product not found"}), 404
        rec_result = recommender_engine.recommend_for_items([product["name"]], top_n=4)
        return jsonify(
            {
                "product": product,
                "recommendations": rec_result["recommendations"],
                "message": rec_result["message"],
            }
        )

    @app.route("/api/cart")
    def api_cart():
        return jsonify(_build_cart_payload())

    @app.route("/api/cart/add", methods=["POST"])
    def api_cart_add():
        data = request.get_json(silent=True) or request.form
        try:
            product_id = int(data.get("product_id", 0))
            quantity = max(1, int(data.get("quantity", 1)))
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid product or quantity"}), 400

        product = get_product_by_id(product_id)
        if not product:
            return jsonify({"error": "Product does not exist"}), 404

        cart_map = _get_cart_dict()
        key = str(product_id)
        cart_map[key] = min(99, cart_map.get(key, 0) + quantity)
        session["cart"] = cart_map
        session.modified = True

        payload = _build_cart_payload()
        payload["added_product"] = product["name"]
        return jsonify(payload)

    @app.route("/api/cart/update", methods=["POST"])
    def api_cart_update():
        data = request.get_json(silent=True) or request.form
        try:
            product_id = int(data.get("product_id", 0))
            quantity = int(data.get("quantity", 0))
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid parameters"}), 400

        cart_map = _get_cart_dict()
        key = str(product_id)
        if quantity <= 0:
            cart_map.pop(key, None)
        else:
            cart_map[key] = min(99, quantity)
        session["cart"] = cart_map
        session.modified = True
        return jsonify(_build_cart_payload())

    @app.route("/api/cart/remove", methods=["POST"])
    def api_cart_remove():
        data = request.get_json(silent=True) or request.form
        try:
            product_id = int(data.get("product_id", 0))
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid product id"}), 400

        cart_map = _get_cart_dict()
        cart_map.pop(str(product_id), None)
        session["cart"] = cart_map
        session.modified = True
        return jsonify(_build_cart_payload())

    @app.route("/api/cart/clear", methods=["POST"])
    def api_cart_clear():
        session["cart"] = {}
        session.modified = True
        return jsonify(_build_cart_payload())

    @app.route("/api/checkout", methods=["POST"])
    def api_checkout():
        cart_payload = _build_cart_payload()
        if not cart_payload["items"]:
            return jsonify({"error": "Your shopping cart is empty."}), 400

        user_id = int(session["user_id"]) if session.get("user_id") else None
        order = save_checkout_transaction(user_id=user_id, cart_items=cart_payload["items"])

        # Clear cart and refresh Apriori model with the new transaction
        session["cart"] = {}
        session.modified = True
        recommender_engine.train()

        return jsonify(
            {
                "success": True,
                "order": order,
                "cart": _build_cart_payload(),
                "message": "Transaction saved to SQLite and Apriori model updated!",
            }
        )

    @app.route("/api/recommend", methods=["POST"])
    def api_recommend():
        data = request.get_json(silent=True) or {}
        selected = data.get("items", [])
        if not isinstance(selected, list):
            return jsonify({"error": "items must be a list of product names"}), 400

        min_support = data.get("min_support")
        min_confidence = data.get("min_confidence")
        top_n = int(data.get("top_n", 6))

        try:
            sup_val = float(min_support) if min_support is not None else None
            conf_val = float(min_confidence) if min_confidence is not None else None
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid threshold parameter"}), 400

        result = recommender_engine.recommend_for_items(
            selected_items=selected,
            top_n=top_n,
            min_support=sup_val,
            min_confidence=conf_val,
        )
        # Also return updated top rules for the current threshold
        result["top_rules"] = recommender_engine.get_top_rules(limit=15)
        result["frequent_itemsets"] = recommender_engine.get_frequent_itemsets(min_len=2, limit=12)
        return jsonify(result)

    @app.route("/api/dashboard-data")
    def api_dashboard_data():
        return jsonify(compute_dashboard_analytics())

    @app.errorhandler(404)
    def page_not_found(_err):
        return render_template("404.html"), 404

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
