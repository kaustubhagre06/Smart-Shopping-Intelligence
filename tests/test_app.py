"""Comprehensive integration tests for Smart Shopping Intelligence System."""

import unittest

from app import app
from database.db import get_connection
from ml.recommendation import recommender_engine


class SmartShopTestCase(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_01_all_public_routes_return_200(self):
        routes = ["/", "/login", "/register", "/products", "/product/1", "/cart", "/recommendations", "/dashboard", "/about"]
        for route in routes:
            res = self.client.get(route)
            self.assertEqual(res.status_code, 200, f"Route {route} failed with {res.status_code}")

        res_404 = self.client.get("/non-existent-route")
        self.assertEqual(res_404.status_code, 404)

    def test_02_products_catalog_and_filters(self):
        res = self.client.get("/api/products")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertGreaterEqual(data["count"], 36)

        res_search = self.client.get("/api/products?q=Bread")
        self.assertTrue(any(p["name"] == "Bread" for p in res_search.get_json()["products"]))

        res_cat = self.client.get("/api/products?category=Dairy+%26+Eggs")
        dairy = res_cat.get_json()["products"]
        self.assertEqual(len(dairy), 6)
        self.assertTrue(all(p["category"] == "Dairy & Eggs" for p in dairy))

    def test_03_apriori_recommendations(self):
        res = self.client.post("/api/recommend", json={"items": ["Bread"]})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertGreater(len(data["recommendations"]), 0)
        names = [r["product"]["name"] for r in data["recommendations"]]
        self.assertIn("Butter", names)
        self.assertIn("Customers who bought Bread", data["recommendations"][0]["explanation"])

        # Empty basket graceful handling
        res_empty = self.client.post("/api/recommend", json={"items": []})
        self.assertEqual(res_empty.status_code, 200)
        self.assertEqual(res_empty.get_json()["recommendations"], [])
        self.assertTrue(len(res_empty.get_json()["message"]) > 0)

        # Unachievable threshold graceful handling
        res_strict = self.client.post(
            "/api/recommend",
            json={"items": ["Bread"], "min_support": 0.75, "min_confidence": 0.99},
        )
        self.assertEqual(res_strict.status_code, 200)
        self.assertEqual(res_strict.get_json()["recommendations"], [])

        # Restore default thresholds
        recommender_engine.train(min_support=0.025, min_confidence=0.25, min_lift=1.05)

    def test_04_register_login_logout_flow(self):
        test_email = "test_student@smartshop.ai"
        conn = get_connection()
        conn.execute("DELETE FROM users WHERE email = ?", (test_email,))
        conn.commit()
        conn.close()

        # Invalid registration (mismatched passwords)
        bad_reg = self.client.post(
            "/register",
            data={
                "full_name": "Test Student",
                "email": test_email,
                "password": "Password1",
                "confirm_password": "Password2",
            },
        )
        self.assertIn(b"Passwords do not match", bad_reg.data)

        # Valid registration
        ok_reg = self.client.post(
            "/register",
            data={
                "full_name": "Test Student",
                "email": test_email,
                "password": "Password1",
                "confirm_password": "Password1",
            },
            follow_redirects=True,
        )
        self.assertEqual(ok_reg.status_code, 200)
        self.assertIn(b"Test Student", ok_reg.data)

        # Logout
        self.client.get("/logout", follow_redirects=True)

        # Login with created account
        ok_login = self.client.post(
            "/login",
            data={"email": test_email, "password": "Password1"},
            follow_redirects=True,
        )
        self.assertEqual(ok_login.status_code, 200)
        self.assertIn(b"Test Student", ok_login.data)

    def test_05_cart_and_checkout_persistence(self):
        # Add Bread (id=1) x2 and Butter (id=8) x1
        r1 = self.client.post("/api/cart/add", json={"product_id": 1, "quantity": 2})
        self.assertEqual(r1.status_code, 200)
        r2 = self.client.post("/api/cart/add", json={"product_id": 8, "quantity": 1})
        self.assertEqual(r2.status_code, 200)
        cart = r2.get_json()
        self.assertEqual(cart["item_count"], 3)
        self.assertAlmostEqual(cart["subtotal"], round(3.49 * 2 + 4.29, 2), places=2)

        # Update qty
        r3 = self.client.post("/api/cart/update", json={"product_id": 1, "quantity": 1})
        self.assertEqual(r3.get_json()["item_count"], 2)

        # Checkout
        chk = self.client.post("/api/checkout")
        self.assertEqual(chk.status_code, 200)
        chk_data = chk.get_json()
        self.assertTrue(chk_data["success"])
        self.assertTrue(chk_data["order"]["transaction_code"].startswith("ORD-"))
        self.assertEqual(chk_data["cart"]["item_count"], 0)

        # Verify saved in SQLite & clean up test checkout record
        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM transactions WHERE transaction_code = ?",
            (chk_data["order"]["transaction_code"],),
        ).fetchone()
        self.assertIsNotNone(row)
        conn.execute("DELETE FROM transactions WHERE id = ?", (row["id"],))
        conn.commit()
        conn.close()

    def test_06_dashboard_analytics_api(self):
        res = self.client.get("/api/dashboard-data")
        self.assertEqual(res.status_code, 200)
        payload = res.get_json()
        self.assertGreaterEqual(payload["kpis"]["total_transactions"], 1200)
        self.assertEqual(payload["kpis"]["total_products"], 36)
        for chart_key in [
            "popular_products",
            "category_trends",
            "top_combinations",
            "rules_scatter",
            "cooccurrence_heatmap",
        ]:
            self.assertIn(chart_key, payload["charts"])
            self.assertGreater(len(payload["charts"][chart_key]["data"]), 0)


if __name__ == "__main__":
    unittest.main()
