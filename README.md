# Smart Shopping Intelligence System (SmartShop AI)

A full-stack Machine Learning retail platform demonstrating **Market Basket Analysis** and **Explainable Product Recommendations** using the **Apriori Algorithm**, **Python Flask**, **Pandas/NumPy**, **Plotly**, and **SQLite**.

## Features

- **Home Landing Page (`/`)**: Modern startup UI with live Apriori rule feed, featured products, and category overview.
- **User Authentication (`/register`, `/login`, `/logout`)**: Full form validation, Werkzeug password hashing, and SQLite user persistence.
- **Product Explorer (`/products` & `/product/<id>`)**: 36 curated products across 6 retail categories with local custom SVG illustrations, live search, category pills, sorting, product detail modal, and integrated Apriori recommendations.
- **Shopping Cart & Checkout (`/cart`)**: Quantity controls, item removal, live subtotal/tax/total calculations, cart-aware Apriori suggestions, and SQLite checkout persistence that retrains the ML engine on new orders.
- **Smart Recommendation Engine (`/recommendations`)**: Interactive Apriori workbench with multi-item basket selection, Support/Confidence sliders, natural-language explanations (*"Customers who bought Bread also frequently bought Butter"*), and ranked rule tables.
- **Analytics Dashboard (`/dashboard`)**: Interactive Plotly charts built directly from SQLite transactions (Popular Products, Category Trends, Top Product Combinations, Support vs. Confidence vs. Lift scatter map, and Co-Occurrence Heatmap).
- **About Project (`/about`)**: Problem statement, objectives, Apriori mathematical formulas, ML workflow, and future scope.

## Project Structure

```text
smart-shopping-intelligence/
├── app.py
├── requirements.txt
├── README.md
├── database/
│   ├── __init__.py
│   ├── db.py
│   └── shopping.db          (auto-created on first run)
├── data/
│   ├── generate_data.py
│   ├── products.json
│   └── transactions.csv
├── ml/
│   ├── __init__.py
│   ├── preprocessing.py
│   ├── recommendation.py
│   └── analytics.py
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── products.html
│   ├── product_detail.html
│   ├── cart.html
│   ├── recommendations.html
│   ├── dashboard.html
│   ├── about.html
│   └── 404.html
└── static/
    ├── css/style.css
    ├── js/
    └── images/products/
```

## Setup & Running Locally

1. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   # Windows PowerShell:
   .\venv\Scripts\Activate.ps1
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Generate seed dataset & SVG product assets (optional, also runs automatically on startup)**
   ```bash
   python data/generate_data.py
   ```

4. **Start the Flask server**
   ```bash
   python app.py
   ```

5. **Open in browser**
   Visit `http://127.0.0.1:5000`

   **Demo account**: `demo@smartshop.ai` / `Demo@123` (or register a new user on `/register`).
